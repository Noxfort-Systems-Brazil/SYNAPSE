# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
import os
import shutil
import tempfile

from src.security.password_policy import ModernPasswordPolicy
from src.security.security_manager import SecurityManager
from src.security.audit_logger import AuditLogger
from src.handlers.security_handler import SecurityCommandHandler
from src.ipc.ipc_protocol import IpcMessage


def test_password_policy_valid_passwords():
    policy = ModernPasswordPolicy()
    valid_samples = [
        "Seguranca@2026",
        "Synapse#Core_99",
        "Abcdef1!",
        "V@lidPassw0rd!",
    ]
    for pwd in valid_samples:
        res = policy.validate(pwd)
        assert res.is_valid is True, f"Failed for {pwd}: {res.errors}"
        assert len(res.errors) == 0


def test_password_policy_too_short():
    policy = ModernPasswordPolicy(min_length=8)
    res = policy.validate("Aa1!")
    assert res.is_valid is False
    assert any("no mínimo 8 caracteres" in err for err in res.errors)


def test_password_policy_missing_uppercase():
    policy = ModernPasswordPolicy()
    res = policy.validate("senhaforte@123")
    assert res.is_valid is False
    assert any("letra maiúscula" in err for err in res.errors)


def test_password_policy_missing_lowercase():
    policy = ModernPasswordPolicy()
    res = policy.validate("SENHAFORTE@123")
    assert res.is_valid is False
    assert any("letra minúscula" in err for err in res.errors)


def test_password_policy_missing_digits():
    policy = ModernPasswordPolicy()
    res = policy.validate("SenhaForte@SemNumero")
    assert res.is_valid is False
    assert any("pelo menos um número" in err for err in res.errors)


def test_password_policy_missing_special_chars():
    policy = ModernPasswordPolicy()
    res = policy.validate("SenhaForte1234")
    assert res.is_valid is False
    assert any("caractere especial" in err for err in res.errors)


def test_password_policy_surrounding_whitespace():
    policy = ModernPasswordPolicy()
    res = policy.validate(" SenhaForte@123 ")
    assert res.is_valid is False
    assert any("espaços" in err for err in res.errors)


def test_password_policy_empty_or_none():
    policy = ModernPasswordPolicy()
    res_empty = policy.validate("")
    assert res_empty.is_valid is False
    assert any("vazia" in err for err in res_empty.errors)


def test_password_strength_calculation():
    policy = ModernPasswordPolicy()
    assert policy.calculate_strength("") == 0
    assert policy.calculate_strength("abc") <= 1
    assert policy.calculate_strength("abcdefgh") >= 1
    assert policy.calculate_strength("Abcdefgh1") >= 3
    assert policy.calculate_strength("Abcdefgh1!@#") == 4


@pytest.fixture
def temp_sec_dir():
    temp_dir = tempfile.mkdtemp(prefix="synapse_sec_policy_test_")
    yield temp_dir
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


def test_security_manager_enforces_password_policy(temp_sec_dir):
    sec = SecurityManager(config_dir=temp_sec_dir)

    # Weak password rejected
    assert sec.add_user("weak_user", "123", "OPERATOR") is False
    assert "no mínimo 8 caracteres" in (sec.get_last_account_error() or "")

    # Valid modern password accepted
    assert sec.add_user("valid_user", "ValidPass#2026", "OPERATOR") is True
    ok, role = sec.authenticate("valid_user", "ValidPass#2026")
    assert ok is True
    assert role == "OPERATOR"


def test_security_command_handler_password_validation(temp_sec_dir):
    sec = SecurityManager(config_dir=temp_sec_dir)
    aud = AuditLogger(config_dir=temp_sec_dir)
    emitter = lambda ev, data=None: None
    handler = SecurityCommandHandler(sec, aud, emitter)

    responses = []
    responder = lambda ok, res=None, err=None: responses.append((ok, res, err))

    # Test standalone validate_password IPC action
    handler.handle_validate_password(
        IpcMessage(action="validate_password", payload={"password": "weak"}),
        responder
    )
    assert responses[-1][0] is True
    assert responses[-1][1]["is_valid"] is False
    assert len(responses[-1][1]["errors"]) > 0

    # Test add_user with weak password
    handler.handle_add_user(
        IpcMessage(action="add_user", payload={"username": "bob", "password": "weak", "role": "OPERATOR"}),
        responder
    )
    assert responses[-1][0] is False
    assert "requisitos de segurança" in responses[-1][2]

    # Test add_user with strong password
    handler.handle_add_user(
        IpcMessage(action="add_user", payload={"username": "bob", "password": "SafeUser#2026", "role": "OPERATOR"}),
        responder
    )
    assert responses[-1][0] is True
    assert responses[-1][1]["success"] is True
