# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
from typing import Dict, Any, List, Tuple, Optional

from src.security.interfaces import (
    IPasswordHasher,
    IUserRepository,
    ISynchronizable,
    IAttemptCounterStore,
    ILockdownManager,
    IAuthenticator,
    IUserManagement,
    IPasswordPolicy,
)
from src.security.models import PasswordValidationResult
from src.security.password_policy import ModernPasswordPolicy
from src.security.config import SecurityConfig, get_user_config_dir

from src.security.crypto import Pbkdf2PasswordHasher
from src.security.lockdown_manager import FileLockdownManager
from src.security.repositories.json_repo import JsonUserRepository
from src.security.repositories.postgres_repo import PostgresUserRepository
from src.security.repositories.hybrid_repo import HybridUserRepository
from src.security.repositories.attempt_store import JsonAttemptStore
from src.security.master_auth import MasterCredentialValidator
from src.security.account_manager import UserAccountManager
from src.utils.logging_setup import get_logger


class SecurityManager(IAuthenticator, IUserManagement):
    """
    High-level facade and orchestrator for the Security Subsystem.
    Coordinates authentication, user accounts, and lockdown rate-limiting
    by delegating to specialized SRP components.
    """

    def __init__(
        self,
        config_dir: Optional[str] = None,
        db_engine: Optional[Any] = None,
        config: Optional[SecurityConfig] = None,
        hasher: Optional[IPasswordHasher] = None,
        lockdown_manager: Optional[ILockdownManager] = None,
        user_repository: Optional[IUserRepository] = None,
        attempt_store: Optional[IAttemptCounterStore] = None,
        password_policy: Optional[IPasswordPolicy] = None,
    ):
        self.logger = get_logger("SecurityManager")

        # 1. Configuration resolution
        self.config = config or SecurityConfig.from_env(config_dir=config_dir)
        self.config_dir = self.config.config_dir
        self.security_file = self.config.security_file
        self.lockdown_file = self.config.lockdown_file
        self.max_failed_attempts = self.config.max_failed_attempts
        self.default_user = self.config.default_user
        self.default_hash = self.config.default_hash
        self.master_user = self.config.master_user
        self.master_hash = self.config.master_hash

        # 2. Cryptographic hasher, Attempt store & Password policy
        self.hasher = hasher or Pbkdf2PasswordHasher()
        self.attempt_store = attempt_store or JsonAttemptStore(self.security_file)
        self.password_policy = password_policy or ModernPasswordPolicy()

        # 3. Database Engine & Persistence Repositories
        if db_engine is not None:
            self.db_engine = db_engine
        elif config_dir is None:
            try:
                from src.database.db_engine import DatabaseEngine
                self.db_engine = DatabaseEngine()
            except Exception as e:
                self.logger.debug(f"Could not auto-initialize DatabaseEngine in SecurityManager: {e}")
                self.db_engine = None
        else:
            self.db_engine = None

        if user_repository is not None:
            self.user_repository = user_repository
            self._local_repo = getattr(user_repository, "local_repo", None)
            self._remote_repo = getattr(user_repository, "remote_repo", None)
        else:
            self._local_repo = JsonUserRepository(self.security_file)
            self._remote_repo = PostgresUserRepository(self.db_engine) if self.db_engine is not None else None
            self.user_repository = HybridUserRepository(self._local_repo, self._remote_repo)

        # 4. Lockdown & Rate Limiting Manager
        if lockdown_manager is not None:
            self.lockdown_manager = lockdown_manager
        else:
            self.lockdown_manager = FileLockdownManager(
                lockdown_file=self.lockdown_file,
                max_failed_attempts=self.max_failed_attempts,
                attempts_getter=self.attempt_store.get_failed_attempts,
                attempts_setter=self.attempt_store.set_failed_attempts,
            )

        # 5. Specialized Delegates (SRP)
        self.master_validator = MasterCredentialValidator(
            master_user=self.master_user,
            master_hash=self.master_hash,
            default_user=self.default_user,
            default_hash=self.default_hash,
        )

        self.account_manager = UserAccountManager(
            user_repository=self.user_repository,
            hasher=self.hasher,
            is_protected_master_fn=self.master_validator.is_protected_master,
            password_policy=self.password_policy,
            db_engine=self.db_engine,
            security_file=self.security_file,
            sync_callback=self._sync_with_db,
            logger=self.logger,
        )

        self.last_auth_user = "SYSTEM"
        self._ensure_files()

    def _ensure_files(self) -> None:
        """Initializes storage backend and synchronizes with database."""
        self.user_repository.ensure_storage()

    def _sync_with_db(self) -> None:
        """Delegates database synchronization to repository if synchronizable."""
        if isinstance(self.user_repository, ISynchronizable):
            self.user_repository.sync()
        else:
            sync_fn = getattr(self.user_repository, "sync", None)
            if callable(sync_fn):
                sync_fn()

    def _load_db(self) -> Dict[str, Any]:
        """Backward compatibility: loads local json database."""
        db = {"users": {}, "failed_attempts": 0}
        load_fn = getattr(self._local_repo, "_load_db", None) if self._local_repo else None
        if callable(load_fn):
            db = load_fn()
        db["failed_attempts"] = self.attempt_store.get_failed_attempts()
        return db

    def _save_db(self, db: Dict[str, Any]) -> None:
        """Backward compatibility: saves local json database."""
        save_fn = getattr(self._local_repo, "_save_db", None) if self._local_repo else None
        if callable(save_fn):
            save_fn(db)
        if "failed_attempts" in db:
            self.attempt_store.set_failed_attempts(db["failed_attempts"])

    def _hash_password(self, password: str, salt: Optional[bytes] = None) -> str:
        """Backward compatibility delegation to hasher."""
        return self.hasher.hash_password(password, salt=salt)

    def _verify_password(self, password: str, stored_hash_str: str) -> bool:
        """Backward compatibility delegation to hasher."""
        return self.hasher.verify_password(password, stored_hash_str)

    def is_lockdown(self) -> bool:
        """Returns True if the system is currently under persistent lockdown."""
        return self.lockdown_manager.is_lockdown()

    def trigger_lockdown(self) -> None:
        """Triggers persistent lockdown state."""
        self.lockdown_manager.trigger_lockdown()

    def clear_lockdown(self) -> None:
        """Removes persistent lockdown and resets failed attempts."""
        self.lockdown_manager.clear_lockdown()

    def record_failed_attempt(self) -> bool:
        """Records failed attempt and triggers lockdown if threshold reached."""
        return self.lockdown_manager.record_failed_attempt()

    def authenticate(self, username: str, password: str) -> Tuple[bool, str]:
        """
        Attempts to authenticate a user.
        Returns: (success_bool, role_string_or_error_msg)
        """
        invalid_msg = "Credenciais inválidas."
        system_locked_msg = "SISTEMA BLOQUEADO. Apenas Super Usuários podem desbloquear."

        # 1. Master Fallback Check (God mode)
        is_master, is_attempt = self.master_validator.verify_master(username, password)
        if is_master:
            self.last_auth_user = username
            if self.is_lockdown():
                self.clear_lockdown()
            return True, "MASTER"
        elif is_attempt:
            self.record_failed_attempt()
            return False, invalid_msg

        users = self.user_repository.fetch_users()

        # 2. Lockdown handling: only SUPERUSER or MASTER can unlock
        if self.is_lockdown():
            if username not in users and self.db_engine:
                self._sync_with_db()
                users = self.user_repository.fetch_users()

            if username in users:
                user_data = users[username]
                if user_data.get("role") == "SUPERUSER":
                    if self.hasher.verify_password(password, user_data.get("hash", "")):
                        self.last_auth_user = username
                        self.clear_lockdown()
                        return True, "SUPERUSER"

            return False, system_locked_msg

        # 3. Standard authentication
        if username not in users and self.db_engine:
            self._sync_with_db()
            users = self.user_repository.fetch_users()

        if username not in users:
            self.record_failed_attempt()
            return False, invalid_msg

        user_data = users[username]
        if self.hasher.verify_password(password, user_data.get("hash", "")):
            self.last_auth_user = username
            reset_fn = getattr(self.lockdown_manager, "reset_attempts", None)
            if callable(reset_fn):
                reset_fn()
            return True, user_data.get("role", "OPERATOR")
        else:
            self.record_failed_attempt()
            return False, invalid_msg

    def add_user(self, username: str, password: str, role: str) -> bool:
        """Creates a new user with the specified role."""
        return self.account_manager.add_user(username, password, role)

    def remove_user(self, username: str) -> bool:
        """Removes an existing user. Blocked for master users."""
        return self.account_manager.remove_user(username)

    def list_users(self) -> List[Dict[str, str]]:
        """Returns the list of registered users and their roles (excluding passwords)."""
        return self.account_manager.list_users()

    def validate_password(self, password: str) -> PasswordValidationResult:
        """Validates password against system password security policy."""
        return self.password_policy.validate(password)

    def get_last_account_error(self) -> Optional[str]:
        """Returns the last error message from user account operations."""
        return getattr(self.account_manager, "last_error", None)

