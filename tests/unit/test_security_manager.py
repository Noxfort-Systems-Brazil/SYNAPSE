# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Security Subsystem Unit Test Suite Aggregator (SOLID & Clean Architecture).
Delegates tests across modular suites under tests/unit/security/:
- test_security_core.py: Authentication, master fallback, custom env, and user CRUD.
- test_security_handlers.py: IPC command handlers and lockdown rejection.
- test_security_audit.py: Audit logging, database persistence, and offline resilience.
"""

from tests.unit.security.test_security_core import (
    temp_sec_dir,
    test_security_manager_initialization_no_default_user,
    test_security_manager_master_user_authentication,
    test_security_manager_custom_env_credentials,
    test_security_manager_lockdown_failsafe,
    test_security_manager_user_crud,
)
from tests.unit.security.test_security_handlers import (
    test_security_command_handler,
    test_system_handler_lockdown_rejection,
    test_system_and_source_handler_audit_logging,
)
from tests.unit.security.test_security_audit import (
    test_audit_logger,
    test_audit_logger_database_and_telemetry_reporting,
    test_security_manager_database_synchronization_and_folder_deletion_recovery,
    test_security_manager_resilience_when_database_offline,
)

__all__ = [
    "temp_sec_dir",
    "test_security_manager_initialization_no_default_user",
    "test_security_manager_master_user_authentication",
    "test_security_manager_custom_env_credentials",
    "test_security_manager_lockdown_failsafe",
    "test_security_manager_user_crud",
    "test_security_command_handler",
    "test_system_handler_lockdown_rejection",
    "test_system_and_source_handler_audit_logging",
    "test_audit_logger",
    "test_audit_logger_database_and_telemetry_reporting",
    "test_security_manager_database_synchronization_and_folder_deletion_recovery",
    "test_security_manager_resilience_when_database_offline",
]
