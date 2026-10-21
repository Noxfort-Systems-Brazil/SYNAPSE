# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: src/handlers/parquet_handler.py
# Author: Gabriel Moraes
# Date: 2026-09-14

import os
import threading
from typing import Any, Callable, Optional

from src.ipc.ipc_protocol import IpcMessage
from src.ipc.command_router import Responder
from src.services.data_inspection_service import DataInspectionService


class ParquetCommandHandler:
    """Handles Parquet schema inspection and background Parquet dataset ingestion."""

    def __init__(
        self,
        controller: Any,
        event_emitter: Callable[[str, Any], None],
        data_inspection_service: Optional[DataInspectionService] = None,
        importer_factory: Optional[Callable[[Any], Any]] = None,
    ):
        self.controller = controller
        self.event_emitter = event_emitter
        self.data_inspection_service = data_inspection_service or DataInspectionService()
        self._importer_factory = importer_factory or self._default_importer_factory

    @staticmethod
    def _default_importer_factory(storage: Any) -> Any:
        from src.services.database_importer import DatabaseImporter
        return DatabaseImporter(storage)

    def handle_inspect_parquet(self, msg: IpcMessage, responder: Responder) -> None:
        path = msg.payload.get("path", "")
        try:
            info = self.data_inspection_service.inspect_parquet(path)
            responder(True, info)
        except Exception as err:
            responder(False, error=str(err))

    def handle_import_parquet(self, msg: IpcMessage, responder: Responder) -> None:
        raw_path = msg.payload.get("path", "")
        path = os.path.expanduser(raw_path.strip().strip('"\'')) if raw_path else ""

        if not path or not os.path.exists(path):
            responder(False, error=f"Arquivo Parquet não encontrado: {path}")
            return

        storage = getattr(self.controller, "storage", None)
        importer = self._importer_factory(storage)

        def _on_progress(p: int):
            self.event_emitter("import_progress", {"progress": p})

        def _on_log(m: str):
            self.event_emitter("log_message", {"message": m, "level": "INFO"})

        def _on_finished(ok: bool, m: str):
            self.event_emitter("import_finished", {"success": ok, "message": m})

        importer.on_progress = _on_progress
        importer.on_log = _on_log
        importer.on_finished = _on_finished

        for sig_name, cb in (
            ("progress_update", _on_progress),
            ("log_message", _on_log),
            ("import_finished", lambda ok, m: _on_finished(ok, m)),
        ):
            sig_obj = getattr(importer, sig_name, None)
            connect_fn = getattr(sig_obj, "connect", None)
            if callable(connect_fn):
                try:
                    connect_fn(cb)
                except Exception:
                    pass

        exec_fn = getattr(importer, "execute_import", None)
        if callable(exec_fn):
            threading.Thread(target=exec_fn, args=(path,), daemon=True).start()

        responder(True, {"status": "import_started", "path": path})
