# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: src/handlers/database_handler.py
# Author: Gabriel Moraes
# Date: 2026-08-30

"""
Database & Analytics Storage Command Handler (SOLID: SRP & DIP Facade).
Delegates to ParquetCommandHandler and PostgresCommandHandler (Flat src/handlers layout).
"""

from typing import Any, Callable, Optional

from src.ipc.ipc_protocol import IpcMessage
from src.ipc.command_router import Responder
from src.services.data_inspection_service import DataInspectionService
from src.handlers.parquet_handler import ParquetCommandHandler
from src.handlers.postgres_handler import PostgresCommandHandler


class DatabaseCommandHandler:
    """Facade translating IPC actions for Parquet datasets and PostgreSQL operations."""

    def __init__(
        self,
        controller: Any,
        event_emitter: Callable[[str, Any], None],
        data_inspection_service: Optional[DataInspectionService] = None,
        importer_factory: Optional[Callable[[Any], Any]] = None,
        postgres_worker_factory: Optional[Callable[[], Any]] = None,
        postgres_manager_factory: Optional[Callable[[], Any]] = None,
    ):
        self.controller = controller
        self.event_emitter = event_emitter

        self.parquet_handler = ParquetCommandHandler(
            controller=controller,
            event_emitter=event_emitter,
            data_inspection_service=data_inspection_service,
            importer_factory=importer_factory,
        )

        self.postgres_handler = PostgresCommandHandler(
            controller=controller,
            worker_factory=postgres_worker_factory,
            manager_factory=postgres_manager_factory,
        )

    def handle_inspect_parquet(self, msg: IpcMessage, responder: Responder) -> None:
        self.parquet_handler.handle_inspect_parquet(msg, responder)

    def handle_import_parquet(self, msg: IpcMessage, responder: Responder) -> None:
        self.parquet_handler.handle_import_parquet(msg, responder)

    def handle_test_db_connection(self, msg: IpcMessage, responder: Responder) -> None:
        self.postgres_handler.handle_test_db_connection(msg, responder)

    def handle_initialize_db(self, msg: IpcMessage, responder: Responder) -> None:
        self.postgres_handler.handle_initialize_db(msg, responder)

    def handle_get_database_config(self, msg: IpcMessage, responder: Responder) -> None:
        self.postgres_handler.handle_get_database_config(msg, responder)

    def handle_disconnect_db(self, msg: IpcMessage, responder: Responder) -> None:
        self.postgres_handler.handle_disconnect_db(msg, responder)

    def handle_get_telemetry_config(self, msg: IpcMessage, responder: Responder) -> None:
        self.postgres_handler.handle_get_telemetry_config(msg, responder)

    def handle_save_telemetry_config(self, msg: IpcMessage, responder: Responder) -> None:
        self.postgres_handler.handle_save_telemetry_config(msg, responder)

    def handle_test_telemetry_connection(self, msg: IpcMessage, responder: Responder) -> None:
        self.postgres_handler.handle_test_telemetry_connection(msg, responder)
