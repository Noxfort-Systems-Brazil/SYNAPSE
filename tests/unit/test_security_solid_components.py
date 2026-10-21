# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Unit Tests for Refactored SOLID Security Subsystem Components.
Tests IPasswordHasher, FileLockdownManager, JsonUserRepository,
PostgresUserRepository, HybridUserRepository, JsonAttemptStore,
and Dependency Injection on SecurityManager.
"""

import os
import shutil
import tempfile
import pytest
from unittest.mock import MagicMock

from src.security.interfaces import (
    IPasswordHasher,
    IUserRepository,
    ISynchronizable,
    IAttemptCounterStore,
    ILockdownManager,
    IAuthenticator,
    IUserManagement,
)
from src.security.crypto import Pbkdf2PasswordHasher, Sha256Hasher
from src.security.lockdown_manager import FileLockdownManager
from src.security.repositories.json_repo import JsonUserRepository
from src.security.repositories.postgres_repo import PostgresUserRepository
from src.security.repositories.hybrid_repo import HybridUserRepository
from src.security.repositories.attempt_store import (
    JsonAttemptStore,
    MemoryAttemptStore,
)
from src.security.config import SecurityConfig
from src.security.security_manager import SecurityManager
from src.security.models import UserRole, User, AuthResult


@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp(prefix="synapse_solid_test_")
    yield d
    if os.path.exists(d):
        shutil.rmtree(d)


def test_crypto_hasher():
    hasher = Pbkdf2PasswordHasher(iterations=1000)
    assert isinstance(hasher, IPasswordHasher)

    hashed = hasher.hash_password("Secret123")
    assert ":" in hashed
    assert hasher.verify_password("Secret123", hashed) is True
    assert hasher.verify_password("WrongPassword", hashed) is False
    assert hasher.verify_password("Secret123", "malformed_hash") is False

    # SHA256 helper
    h_sha = Sha256Hasher.hash_password("admin")
    assert Sha256Hasher.verify_password("admin", h_sha) is True
    assert Sha256Hasher.verify_password("wrong", h_sha) is False


def test_file_lockdown_manager(temp_dir):
    flag_file = os.path.join(temp_dir, "lockdown.flag")
    lockdown = FileLockdownManager(lockdown_file=flag_file, max_failed_attempts=2)
    assert isinstance(lockdown, ILockdownManager)

    assert lockdown.is_lockdown() is False
    assert lockdown.record_failed_attempt() is False  # 1/2
    assert lockdown.is_lockdown() is False

    assert lockdown.record_failed_attempt() is True   # 2/2 -> Triggered!
    assert lockdown.is_lockdown() is True
    assert os.path.isfile(flag_file)

    lockdown.clear_lockdown()
    assert lockdown.is_lockdown() is False
    assert not os.path.isfile(flag_file)


def test_attempt_stores(temp_dir):
    # JsonAttemptStore
    sec_file = os.path.join(temp_dir, "security.json")
    store = JsonAttemptStore(sec_file)
    assert isinstance(store, IAttemptCounterStore)
    assert store.get_failed_attempts() == 0
    store.set_failed_attempts(3)
    assert store.get_failed_attempts() == 3

    # MemoryAttemptStore
    mem_store = MemoryAttemptStore(initial_count=1)
    assert isinstance(mem_store, IAttemptCounterStore)
    assert mem_store.get_failed_attempts() == 1
    mem_store.set_failed_attempts(0)
    assert mem_store.get_failed_attempts() == 0


def test_json_user_repository(temp_dir):
    sec_file = os.path.join(temp_dir, "security.json")
    repo = JsonUserRepository(sec_file)
    assert isinstance(repo, IUserRepository)

    repo.ensure_storage()
    assert os.path.exists(sec_file)
    assert len(repo.fetch_users()) == 0

    assert repo.save_user("alice", "hash_alice", "OPERATOR") is True
    users = repo.fetch_users()
    assert "alice" in users
    assert users["alice"]["role"] == "OPERATOR"

    # Delete
    assert repo.delete_user("alice") is True
    assert "alice" not in repo.fetch_users()
    assert repo.delete_user("alice") is False


def test_postgres_user_repository_offline_resilience():
    mock_engine = MagicMock()
    mock_engine.get_connection.return_value = None
    mock_engine.is_connected = False

    pg_repo = PostgresUserRepository(mock_engine)
    assert isinstance(pg_repo, IUserRepository)
    assert pg_repo.fetch_users() == {}
    assert pg_repo.save_user("test", "hash", "OPERATOR") is False
    assert pg_repo.delete_user("test") is False


def test_hybrid_user_repository_sync(temp_dir):
    sec_file = os.path.join(temp_dir, "security.json")
    local_repo = JsonUserRepository(sec_file)
    local_repo.ensure_storage()

    mock_engine = MagicMock()
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_engine.get_connection.return_value = mock_conn
    mock_engine.is_connected = True
    mock_conn.cursor.return_value = mock_cur

    # Mock DB returns one user 'bob'
    mock_cur.fetchall.return_value = [("bob", "hash_bob", "SUPERUSER")]

    pg_repo = PostgresUserRepository(mock_engine)
    hybrid_repo = HybridUserRepository(local_repo, pg_repo)
    assert isinstance(hybrid_repo, IUserRepository)
    assert isinstance(hybrid_repo, ISynchronizable)

    # Sync restores bob into local_repo
    hybrid_repo.sync()
    local_users = local_repo.fetch_users()
    assert "bob" in local_users
    assert local_users["bob"]["role"] == "SUPERUSER"


def test_security_manager_dependency_injection(temp_dir):
    """
    Demonstrates Dependency Inversion (DIP):
    SecurityManager can be fully tested with in-memory mocks without I/O or DB.
    """
    mock_repo = MagicMock()
    mock_repo.fetch_users.return_value = {
        "mock_user": {"hash": "mock_hash", "role": "OPERATOR"}
    }

    mock_hasher = MagicMock()
    mock_hasher.verify_password.return_value = True
    mock_hasher.hash_password.return_value = "generated_hash"

    mock_lockdown = MagicMock()
    mock_lockdown.is_lockdown.return_value = False

    mock_attempts = MagicMock()
    mock_attempts.get_failed_attempts.return_value = 0

    config = SecurityConfig(
        config_dir=temp_dir,
        security_file=os.path.join(temp_dir, "sec.json"),
        lockdown_file=os.path.join(temp_dir, "lock.flag"),
        master_user="admin",
        master_hash=Sha256Hasher.hash_password("admin"),
    )

    sec = SecurityManager(
        config=config,
        hasher=mock_hasher,
        lockdown_manager=mock_lockdown,
        user_repository=mock_repo,
        attempt_store=mock_attempts,
    )

    assert isinstance(sec, IAuthenticator)
    assert isinstance(sec, IUserManagement)

    # Authenticate delegated to mock_hasher and mock_repo
    ok, role = sec.authenticate("mock_user", "any_pwd")
    assert ok is True
    assert role == "OPERATOR"
    mock_hasher.verify_password.assert_called_once_with("any_pwd", "mock_hash")


def test_models_and_enums():
    assert UserRole.is_valid_assignable_role("OPERATOR") is True
    assert UserRole.is_valid_assignable_role("SUPERUSER") is True
    assert UserRole.is_valid_assignable_role("MASTER") is False
    assert UserRole.is_valid_assignable_role("INVALID") is False

    user = User(username="carol", password_hash="h123", role="OPERATOR")
    assert user.username == "carol"
    assert user.role == "OPERATOR"

    res = AuthResult(success=True, role_or_error="SUPERUSER")
    assert res.success is True
