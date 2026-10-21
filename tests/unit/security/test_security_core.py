# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import shutil
import tempfile
import pytest

from src.security.security_manager import SecurityManager


@pytest.fixture
def temp_sec_dir():
    temp_dir = tempfile.mkdtemp(prefix="synapse_sec_test_")
    yield temp_dir
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


def test_security_manager_initialization_no_default_user(temp_sec_dir):
    """Ensures no custom user accounts are written by default. Clean state."""
    sec = SecurityManager(config_dir=temp_sec_dir)
    assert os.path.isfile(sec.security_file)
    users = sec.list_users()
    assert len(users) == 0


def test_security_manager_master_user_authentication(temp_sec_dir):
    """Verifies that the default master superuser (admin/admin) authenticates with role MASTER."""
    sec = SecurityManager(config_dir=temp_sec_dir)

    success, role = sec.authenticate("admin", "admin")
    assert success is True
    assert role == "MASTER"

    fail, err = sec.authenticate("admin", "wrong_pass")
    assert fail is False
    assert "Credenciais inválidas" in err


def test_security_manager_custom_env_credentials(temp_sec_dir, monkeypatch):
    """Verifies that master superuser can be customized via environment variables (.env)."""
    monkeypatch.setenv("SYNAPSE_SUPERUSER", "custom_operator")
    monkeypatch.setenv("SYNAPSE_SUPERUSER_PASSWORD", "CustomSafePass@123")
    sec = SecurityManager(config_dir=temp_sec_dir)
    assert sec.master_user == "custom_operator"

    ok_custom, role_custom = sec.authenticate("custom_operator", "CustomSafePass@123")
    assert ok_custom is True
    assert role_custom == "MASTER"

    ok_admin, role_admin = sec.authenticate("admin", "admin")
    assert ok_admin is True
    assert role_admin == "MASTER"


def test_security_manager_lockdown_failsafe(temp_sec_dir):
    """Verifies that 3 failed attempts trigger lockdown, and only master superuser can unlock."""
    sec = SecurityManager(config_dir=temp_sec_dir)
    assert sec.is_lockdown() is False

    sec.authenticate("unknown_user", "bad1")
    assert sec.is_lockdown() is False

    sec.authenticate("unknown_user", "bad2")
    assert sec.is_lockdown() is False

    sec.authenticate("unknown_user", "bad3")
    assert sec.is_lockdown() is True
    assert os.path.isfile(sec.lockdown_file)

    sec.add_user("operator1", "Pass123!@#", "OPERATOR")
    ok, msg = sec.authenticate("operator1", "Pass123!@#")
    assert ok is False
    assert "SISTEMA BLOQUEADO" in msg

    ok_unlock, role = sec.authenticate("admin", "admin")
    assert ok_unlock is True
    assert role == "MASTER"
    assert sec.is_lockdown() is False
    assert not os.path.isfile(sec.lockdown_file)


def test_security_manager_user_crud(temp_sec_dir):
    """Verifies adding and removing users, and ensuring master_user cannot be removed."""
    sec = SecurityManager(config_dir=temp_sec_dir)

    assert sec.add_user("op_john", "Pass_john#2026", "OPERATOR") is True
    assert sec.add_user("op_john", "Pass_john#2026_2", "OPERATOR") is False
    assert sec.add_user("guest", "Pass#1234", "INVALID_ROLE") is False

    users = sec.list_users()
    assert len(users) == 1
    assert users[0]["username"] == "op_john"
    assert users[0]["role"] == "OPERATOR"

    ok, role = sec.authenticate("op_john", "Pass_john#2026")
    assert ok is True
    assert role == "OPERATOR"


    assert sec.remove_user("admin") is False
    assert sec.remove_user("op_john") is True
    assert len(sec.list_users()) == 0
