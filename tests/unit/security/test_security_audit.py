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
from src.handlers.source_handler import SourceCommandHandler
from src.ipc.ipc_protocol import IpcMessage


@pytest.fixture
def temp_sec_dir():
    temp_dir = tempfile.mkdtemp(prefix="synapse_sec_test_")
    yield temp_dir
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


def test_audit_logger(temp_sec_dir):
    aud = AuditLogger(config_dir=temp_sec_dir)
    aud.log_action("admin", "SYSTEM_ACCESS", "Testing audit logger")
    logs = aud.get_logs(limit=10)
    assert len(logs) == 1
    assert logs[0]["username"] == "admin"
    assert logs[0]["action"] == "SYSTEM_ACCESS"


def test_audit_logger_database_and_telemetry_reporting(temp_sec_dir):
    from src.database.db_engine import DatabaseEngine

    db_engine = DatabaseEngine(custom_config={"db_type": "postgres", "schema": "schema_synapse_test"}, auto_init=True)
    
    conn = db_engine.get_connection()
    assert conn is not None
    cur = conn.cursor()
    cur.execute("TRUNCATE TABLE schema_synapse_test.security_audit_logs RESTART IDENTITY;")
    conn.commit()
    conn.close()

    aud = AuditLogger(config_dir=temp_sec_dir, db_engine=db_engine)
    aud.log_action("test_user", "TEST_DB_ACTION", "Testing database persistence")

    db_logs = aud.get_logs(limit=5)
    assert any(l["action"] == "TEST_DB_ACTION" and l["username"] == "test_user" for l in db_logs)

    sec = SecurityManager(config_dir=temp_sec_dir)
    telemetry = MagicMock()
    handler = SecurityCommandHandler(
        security_manager=sec, audit_logger=aud, telemetry_service=telemetry
    )

    responses = []
    responder = lambda ok, res=None, err=None: responses.append((ok, res, err))

    # 1. Failed login -> reports incident WARNING
    handler.handle_authenticate(
        IpcMessage(action="authenticate", payload={"username": "hacker", "password": "wrong"}),
        responder
    )
    assert telemetry.report_incident.called
    pos_args = telemetry.report_incident.call_args[0]
    assert pos_args[0] == "SOFTWARE"
    assert pos_args[1] == "WARNING"
    assert "hacker" in pos_args[2]

    # 2. Trigger lockdown -> reports incident CRITICAL
    handler.handle_authenticate(
        IpcMessage(action="authenticate", payload={"username": "hacker", "password": "wrong"}),
        responder
    )
    handler.handle_authenticate(
        IpcMessage(action="authenticate", payload={"username": "hacker", "password": "wrong"}),
        responder
    )
    assert sec.is_lockdown() is True
    pos_args_lock = telemetry.report_incident.call_args[0]
    assert pos_args_lock[1] == "CRITICAL"
    assert "LOCKDOWN" in pos_args_lock[2]

    # 3. Unlock -> reports incident INFO
    handler.handle_authenticate(
        IpcMessage(action="authenticate", payload={"username": "admin", "password": "admin"}),
        responder
    )
    pos_args_unlock = telemetry.report_incident.call_args[0]
    assert pos_args_unlock[1] == "INFO"

    # 4. Remove sensor -> reports incident WARNING
    app_state = MagicMock()
    src_handler = SourceCommandHandler(
        app_state, security_manager=sec, audit_logger=aud, telemetry_service=telemetry
    )
    src_handler.handle_remove_source(IpcMessage(action="remove_source", payload={"source_id": "cam_01"}))
    pos_args_sensor = telemetry.report_incident.call_args[0]
    assert pos_args_sensor[1] == "WARNING"
    assert "cam_01" in pos_args_sensor[2]


def test_security_manager_database_synchronization_and_folder_deletion_recovery(temp_sec_dir):
    from src.database.db_engine import DatabaseEngine

    db_engine = DatabaseEngine(custom_config={"db_type": "postgres", "schema": "schema_synapse_test"}, auto_init=True)
    conn = db_engine.get_connection()
    assert conn is not None
    cur = conn.cursor()
    cur.execute("TRUNCATE TABLE schema_synapse_test.synapse_users RESTART IDENTITY;")
    conn.commit()
    conn.close()

    # 1. Initialize SecurityManager with DB
    sec1 = SecurityManager(config_dir=temp_sec_dir, db_engine=db_engine)
    assert len(sec1.list_users()) == 0

    # 2. Add user "operador1"
    ok = sec1.add_user("operador1", "SenhaForte@2026", "OPERATOR")
    assert ok is True

    assert len(sec1.list_users()) == 1
    assert sec1.list_users()[0]["username"] == "operador1"
    auth_ok, role = sec1.authenticate("operador1", "SenhaForte@2026")
    assert auth_ok is True
    assert role == "OPERATOR"

    conn = db_engine.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT username, password_hash, role FROM synapse_users WHERE username = %s;", ("operador1",))
    row = cur.fetchone()
    assert row is not None
    assert row[0] == "operador1"
    assert row[2] == "OPERATOR"
    db_hash = row[1]
    assert sec1._verify_password("SenhaForte@2026", db_hash) is True
    conn.close()

    # 3. Simulate deleting directory
    shutil.rmtree(temp_sec_dir)
    assert not os.path.exists(temp_sec_dir)

    # 4. Re-instantiate
    sec2 = SecurityManager(config_dir=temp_sec_dir, db_engine=db_engine)

    # 5. Verify restored
    assert os.path.exists(sec2.security_file)
    restored_users = sec2.list_users()
    assert len(restored_users) == 1
    assert restored_users[0]["username"] == "operador1"

    # 6. Verify authentication
    auth_ok2, role2 = sec2.authenticate("operador1", "SenhaForte@2026")
    assert auth_ok2 is True
    assert role2 == "OPERATOR"

    # 7. Add second user
    ok_super = sec2.add_user("super_gestor", "GestorMaster#2026", "SUPERUSER")
    assert ok_super is True

    # 8. Remove user
    assert sec2.remove_user("operador1") is True
    assert len(sec2.list_users()) == 1


def test_security_manager_resilience_when_database_offline(temp_sec_dir):
    mock_engine = MagicMock()
    mock_engine.get_connection.return_value = None  # DB offline
    mock_engine.db_type = "postgres"

    sec = SecurityManager(config_dir=temp_sec_dir, db_engine=mock_engine)

    assert sec.add_user("local_user", "LocalPass#2026", "OPERATOR") is True
    assert len(sec.list_users()) == 1

    ok, role = sec.authenticate("local_user", "LocalPass#2026")

    assert ok is True
    assert role == "OPERATOR"

    assert sec.remove_user("local_user") is True
    assert len(sec.list_users()) == 0
