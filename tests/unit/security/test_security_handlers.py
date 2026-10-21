# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import shutil
import tempfile
import pytest
from unittest.mock import MagicMock

from src.security.security_manager import SecurityManager
from src.security.audit_logger import AuditLogger
from src.handlers.security_handler import SecurityCommandHandler
from src.handlers.system_handler import SystemCommandHandler
from src.handlers.source_handler import SourceCommandHandler
from src.ipc.ipc_protocol import IpcMessage


@pytest.fixture
def temp_sec_dir():
    temp_dir = tempfile.mkdtemp(prefix="synapse_sec_test_")
    yield temp_dir
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


def test_security_command_handler(temp_sec_dir):
    sec = SecurityManager(config_dir=temp_sec_dir)
    aud = AuditLogger(config_dir=temp_sec_dir)
    emitter_events = []
    emitter = lambda ev, data=None: emitter_events.append((ev, data))

    handler = SecurityCommandHandler(
        security_manager=sec, audit_logger=aud, event_emitter=emitter
    )

    responses = []
    responder = lambda ok, res=None, err=None: responses.append((ok, res, err))

    # Test authenticate master
    msg_auth = IpcMessage(
        action="authenticate",
        payload={"username": "admin", "password": "admin"}
    )
    handler.handle_authenticate(msg_auth, responder)
    assert len(responses) == 1
    assert responses[0][0] is True
    assert responses[0][1]["role"] == "MASTER"

    # Test check_lockdown
    handler.handle_check_lockdown(IpcMessage(action="check_lockdown"), responder)
    assert responses[-1][0] is True
    assert responses[-1][1]["active"] is False

    # Test add_user rejects weak password
    msg_add_weak = IpcMessage(action="add_user", payload={"username": "alice", "password": "pwd", "role": "OPERATOR"})
    handler.handle_add_user(msg_add_weak, responder)
    assert responses[-1][0] is False
    assert "requisitos de segurança" in responses[-1][2]

    # Test add_user with strong compliant password
    msg_add = IpcMessage(action="add_user", payload={"username": "alice", "password": "SecurePass#2026", "role": "OPERATOR"})
    handler.handle_add_user(msg_add, responder)
    assert responses[-1][0] is True


    handler.handle_list_users(IpcMessage(action="list_users"), responder)
    users = responses[-1][1]["users"]
    assert any(u["username"] == "alice" for u in users)

    # Test remove_user
    msg_rm = IpcMessage(action="remove_user", payload={"username": "alice"})
    handler.handle_remove_user(msg_rm, responder)
    assert responses[-1][0] is True


def test_system_handler_lockdown_rejection(temp_sec_dir):
    sec = SecurityManager(config_dir=temp_sec_dir)
    controller = MagicMock()
    sys_handler = SystemCommandHandler(controller, security_manager=sec)

    controller.start_optimization_flow.return_value = True
    res = sys_handler.handle_start_optimization(IpcMessage(action="start_optimization"))
    assert res["started"] is True

    sec.trigger_lockdown()

    with pytest.raises(RuntimeError, match="LOCKDOWN"):
        sys_handler.handle_start_optimization(IpcMessage(action="start_optimization"))

    with pytest.raises(RuntimeError, match="LOCKDOWN"):
        sys_handler.handle_start_offline_bootstrap(IpcMessage(action="start_offline_bootstrap"))

    with pytest.raises(RuntimeError, match="LOCKDOWN"):
        sys_handler.handle_start_online_operation(IpcMessage(action="start_online_operation"))


def test_system_and_source_handler_audit_logging(temp_sec_dir):
    sec = SecurityManager(config_dir=temp_sec_dir)
    aud = AuditLogger(config_dir=temp_sec_dir)
    controller = MagicMock()
    app_state = MagicMock()

    sec.authenticate("admin", "admin")
    assert sec.last_auth_user == "admin"

    sys_handler = SystemCommandHandler(
        controller, security_manager=sec, audit_logger=aud
    )
    controller.start_optimization_flow.return_value = True
    sys_handler.handle_start_optimization(IpcMessage(action="start_optimization"))

    logs = aud.get_logs(limit=10)
    assert any(
        l["action"] == "START_OPTIMIZATION" and l["username"] == "admin"
        for l in logs
    )

    source_handler = SourceCommandHandler(
        app_state, security_manager=sec, audit_logger=aud
    )
    source_handler.handle_add_source(
        IpcMessage(action="add_source", payload={"name": "Radar_A1", "is_local": True})
    )

    logs_after_source = aud.get_logs(limit=10)
    assert any(
        l["action"] == "ADD_SENSOR" and "Radar_A1" in l["details"]
        for l in logs_after_source
    )
