# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: src/security/account_manager.py
# Description: User identity CRUD and persistence coordinator (SOLID: SRP).

import os
from typing import Dict, Any, List, Optional, Callable
import logging

from src.security.interfaces import IUserRepository, IPasswordHasher, IUserManagement, IPasswordPolicy
from src.security.password_policy import ModernPasswordPolicy
from src.utils.logging_setup import get_logger


class UserAccountManager(IUserManagement):
    """
    Coordinates user registration, removal, and listing across storage tiers.
    Encapsulates role validation, protection of master accounts, and repository sync.
    """

    def __init__(
        self,
        user_repository: IUserRepository,
        hasher: IPasswordHasher,
        is_protected_master_fn: Callable[[str], bool],
        password_policy: Optional[IPasswordPolicy] = None,
        db_engine: Optional[Any] = None,
        security_file: Optional[str] = None,
        sync_callback: Optional[Callable[[], None]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.user_repository = user_repository
        self.hasher = hasher
        self.is_protected_master_fn = is_protected_master_fn
        self.password_policy = password_policy or ModernPasswordPolicy()
        self.db_engine = db_engine
        self.security_file = security_file
        self.sync_callback = sync_callback
        self.logger = logger or get_logger("UserAccountManager")
        self.last_error: Optional[str] = None

    def _sync(self) -> None:
        if self.db_engine and self.sync_callback:
            self.sync_callback()

    def add_user(self, username: str, password: str, role: str) -> bool:
        """Creates a new user with the specified role."""
        self.last_error = None
        if role not in ["OPERATOR", "SUPERUSER"]:
            self.last_error = f"Nível de acesso inválido: '{role}'."
            return False
        if not username or not password:
            self.last_error = "Nome de usuário e senha são obrigatórios."
            return False
        if self.is_protected_master_fn(username):
            self.last_error = f"Nome de usuário '{username}' é reservado pelo sistema."
            return False

        if self.password_policy:
            val_result = self.password_policy.validate(password)
            if not val_result.is_valid:
                self.last_error = "; ".join(val_result.errors)
                self.logger.warning(
                    f"Tentativa de cadastro do usuário '{username}' rejeitada: "
                    f"requisitos de senha não atendidos ({self.last_error})"
                )
                return False

        self._sync()

        users = self.user_repository.fetch_users()
        if username in users:
            self.last_error = f"Usuário '{username}' já existe no sistema."
            return False  # User already exists

        pwd_hash = self.hasher.hash_password(password)
        saved = self.user_repository.save_user(username, pwd_hash, role)
        if saved:
            self.logger.info(f"New user registered: {username} ({role})")
        return saved


    def remove_user(self, username: str) -> bool:
        """Removes an existing user. Blocked for master users."""
        if self.is_protected_master_fn(username):
            self.logger.warning(f"Blocked attempt to remove protected master user '{username}'.")
            return False

        removed = self.user_repository.delete_user(username)
        if removed:
            self.logger.info(f"User removed: {username}")
            return True
        return False

    def list_users(self) -> List[Dict[str, str]]:
        """Returns the list of registered users and their roles (excluding passwords)."""
        if self.db_engine:
            if self.security_file and not os.path.exists(self.security_file):
                self.user_repository.ensure_storage()
            else:
                self._sync()

        users = self.user_repository.fetch_users()
        result = []
        for uname, data in users.items():
            result.append({"username": uname, "role": data.get("role", "OPERATOR")})
        return result
