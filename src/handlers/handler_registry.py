# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Handler Registration Registry (SOLID: SRP & Composition Root).

Encapsulates the wiring and registration of all command handlers into the IPC Command Router.
"""

from typing import Any, Callable, Optional

from src.ipc.command_router import IpcCommandRouter
from src.handlers.system_handler import SystemCommandHandler
from src.handlers.report_handler import ReportCommandHandler
from src.handlers.map_handler import MapCommandHandler
from src.handlers.source_handler import SourceCommandHandler
from src.handlers.database_handler import DatabaseCommandHandler
from src.handlers.dialog_handler import SystemDialogHandler
from src.handlers.security_handler import SecurityCommandHandler
from src.security.security_manager import SecurityManager
from src.security.audit_logger import AuditLogger
from src.infrastructure.dialog_service import NativeDialogService
from src.infrastructure.network_service import NetworkService
from src.services.data_inspection_service import DataInspectionService
from src.handlers.duckdns_handler import DuckDnsHandler


def register_default_command_handlers(
    router: IpcCommandRouter,
    controller: Any,
    app_state: Any,
    event_emitter: Callable[[str, Any], None],
    on_shutdown: Optional[Callable[[], None]] = None,
    map_service: Optional[Any] = None,
    dialog_service: Optional[NativeDialogService] = None,
    network_service: Optional[NetworkService] = None,
    data_inspection_service: Optional[DataInspectionService] = None,
    importer_factory: Optional[Callable[[Any], Any]] = None,
    postgres_worker_factory: Optional[Callable[[], Any]] = None,
    postgres_manager_factory: Optional[Callable[[], Any]] = None,
    security_manager: Optional[SecurityManager] = None,
    audit_logger: Optional[AuditLogger] = None,
) -> None:
    """
    Composition helper that registers all standard command handlers into the router.
    """
    # Database engine for persistent audit logs
    db_engine = None
    try:
        from src.database.db_engine import DatabaseEngine
        db_engine = DatabaseEngine()
    except Exception:
        pass

    sec_mgr = security_manager or SecurityManager(db_engine=db_engine)
    aud_log = audit_logger or AuditLogger(db_engine=db_engine)
    telem_svc = getattr(controller, "telemetry", None)

    system_handler = SystemCommandHandler(
        controller,
        on_shutdown=on_shutdown,
        security_manager=sec_mgr,
        audit_logger=aud_log,
    )
    map_handler = MapCommandHandler(app_state, map_service=map_service)
    source_handler = SourceCommandHandler(
        app_state,
        security_manager=sec_mgr,
        audit_logger=aud_log,
        telemetry_service=telem_svc,
    )
    db_handler = DatabaseCommandHandler(
        controller,
        event_emitter,
        data_inspection_service=data_inspection_service,
        importer_factory=importer_factory,
        postgres_worker_factory=postgres_worker_factory,
        postgres_manager_factory=postgres_manager_factory,
    )
    dialog_handler = SystemDialogHandler(
        dialog_service=dialog_service, network_service=network_service
    )
    security_handler = SecurityCommandHandler(
        security_manager=sec_mgr,
        audit_logger=aud_log,
        event_emitter=event_emitter,
        telemetry_service=telem_svc,
    )

    report_handler = ReportCommandHandler(
        controller=controller,
        audit_logger=aud_log,
    )

    # 1. System Actions
    router.register("ping", system_handler.handle_ping)
    router.register("get_system_status", system_handler.handle_get_system_status)
    router.register("start_optimization", system_handler.handle_start_optimization)
    router.register("stop_optimization", system_handler.handle_stop_optimization)
    router.register("start_offline_bootstrap", system_handler.handle_start_offline_bootstrap)
    router.register("stop_offline_bootstrap", system_handler.handle_stop_offline_bootstrap)
    router.register("start_online_operation", system_handler.handle_start_online_operation)
    router.register("stop_online_operation", system_handler.handle_stop_online_operation)
    router.register("explain_buffer", system_handler.handle_explain_buffer)
    router.register("explain_local", system_handler.handle_explain_local)
    router.register("explain_global", system_handler.handle_explain_global)
    router.register("hot_swap_model", system_handler.handle_hot_swap_model)
    router.register("get_process_health", system_handler.handle_get_process_health)
    router.register("reset_workspace", system_handler.handle_reset_workspace)
    router.register("shutdown", system_handler.handle_shutdown)

    # 2. Report Actions (ABNT / Official Traffic Audit)
    router.register("generate_official_report", report_handler.handle_generate_official_report)
    router.register("export_official_report_docx", report_handler.handle_export_official_report_docx)


    # 2. Map Actions
    router.register("load_map", map_handler.handle_load_map)
    router.register("get_topology", map_handler.handle_get_topology)

    # 3. Source Actions
    router.register("get_sources", source_handler.handle_get_sources)
    router.register("add_source", source_handler.handle_add_source)
    router.register("update_source", source_handler.handle_update_source)
    router.register("associate_source", source_handler.handle_associate_source)
    router.register("toggle_origin", source_handler.handle_toggle_origin)
    router.register("remove_source", source_handler.handle_remove_source)
    router.register("preview_batch_sources", source_handler.handle_preview_batch_sources)
    router.register("import_batch_sources", source_handler.handle_import_batch_sources)

    # 4. Database Actions
    router.register("inspect_parquet", db_handler.handle_inspect_parquet)
    router.register("import_parquet", db_handler.handle_import_parquet)
    router.register("test_db_connection", db_handler.handle_test_db_connection)
    router.register("initialize_db", db_handler.handle_initialize_db)
    router.register("get_database_config", db_handler.handle_get_database_config)
    router.register("disconnect_db", db_handler.handle_disconnect_db)
    router.register("get_telemetry_config", db_handler.handle_get_telemetry_config)
    router.register("save_telemetry_config", db_handler.handle_save_telemetry_config)
    router.register("test_telemetry_connection", db_handler.handle_test_telemetry_connection)

    # 5. Dialog and Diagnostics
    router.register("pick_file", dialog_handler.handle_pick_file)
    router.register("save_file", dialog_handler.handle_save_file)
    router.register("pick_directory", dialog_handler.handle_pick_directory)
    router.register("get_network_info", dialog_handler.handle_get_network_info)

    # 6. Security Actions
    router.register("authenticate", security_handler.handle_authenticate)
    router.register("check_lockdown", security_handler.handle_check_lockdown)
    router.register("list_users", security_handler.handle_list_users)
    router.register("add_user", security_handler.handle_add_user)
    router.register("validate_password", security_handler.handle_validate_password)
    router.register("remove_user", security_handler.handle_remove_user)
    router.register("get_audit_logs", security_handler.handle_get_audit_logs)

    # 7. DuckDNS Dynamic DNS & Reverse Proxy Actions
    duckdns_handler = DuckDnsHandler(controller=controller)
    router.register("get_duckdns_config", duckdns_handler.handle_get_duckdns_config)
    router.register("save_duckdns_config", duckdns_handler.handle_save_duckdns_config)
    router.register("test_duckdns_connection", duckdns_handler.handle_test_duckdns_connection)
    router.register("toggle_duckdns", duckdns_handler.handle_toggle_duckdns)


__all__ = ["register_default_command_handlers"]
