# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
from typing import Any, Dict, Optional

from src.ipc.ipc_protocol import IpcMessage
from src.domain.entities import DataSource, SourceStatus
from src.services.sensor_batch_service import SensorBatchService
from src.handlers.source.source_guard import SourceGuard
from src.handlers.source.source_dto_mapper import SourceDtoMapper


class SourceCommandHandler:
    """Pure Orchestrator handling data source registration, association, and scope toggling."""

    def __init__(
        self,
        app_state: Any,
        security_manager: Optional[Any] = None,
        audit_logger: Optional[Any] = None,
        telemetry_service: Optional[Any] = None,
    ):
        self.app_state = app_state
        self.security_manager = security_manager
        self.audit_logger = audit_logger
        self.telemetry_service = telemetry_service

    def _get_current_user(self) -> str:
        user = getattr(self.security_manager, "last_auth_user", None) if self.security_manager else None
        return user or "SYSTEM"

    def handle_get_sources(self, msg: IpcMessage) -> Dict[str, Any]:
        get_fn = getattr(self.app_state, "get_all_data_sources", None) or getattr(self.app_state, "get_all_sources", None)
        raw_sources = get_fn() if callable(get_fn) else []

        sources_list = [
            SourceDtoMapper.to_summary_dto(s, self.app_state)
            for s in (raw_sources or [])
        ]
        return {"sources": sources_list}

    def handle_add_source(self, msg: IpcMessage) -> Dict[str, Any]:
        payload = msg.payload
        name = payload.get("name", "New Source")
        is_local = payload.get("is_local", True)

        SourceGuard.ensure_local_sensor_prerequisites(is_local)

        conn = payload.get("connection", "")
        stype = SourceDtoMapper.parse_source_type(payload.get("source_type"), is_local)
        src_id = payload.get("id") or f"src_{int(os.urandom(4).hex(), 16)}"

        src = DataSource(
            id=src_id,
            name=name,
            is_local=is_local,
            source_type=stype,
            connection_string=conn,
            status=SourceStatus.QUARANTINE,
        )
        self.app_state.add_data_source(src)

        location = payload.get("location") or payload.get("associated_element")
        if location:
            sources_mgr = getattr(self.app_state, "sources", None)
            if sources_mgr is not None:
                sources_mgr.associate(src.id, location)
            sig = getattr(self.app_state, "data_association_changed", None)
            if sig is not None:
                sig.emit(src.id, location)

        if self.audit_logger:
            self.audit_logger.log_action(
                self._get_current_user(),
                "ADD_SENSOR",
                f"Sensor '{src.name}' ({src.id}) cadastrado como {stype.value}" + (f" na via '{location}'" if location else "")
            )
        return {
            "id": src.id,
            "name": src.name,
            "is_local": src.is_local,
            "source_type": stype.value,
            "associated_element": location,
        }

    def handle_update_source(self, msg: IpcMessage) -> Dict[str, Any]:
        payload = msg.payload
        source_id = payload.get("id") or payload.get("source_id")
        if not source_id:
            raise ValueError("ID da fonte obrigatório para atualização.")

        name = payload.get("name")
        is_local = payload.get("is_local")

        if is_local is True:
            SourceGuard.ensure_local_sensor_prerequisites(True)

        conn = payload.get("connection") or payload.get("connection_string")
        raw_stype = payload.get("source_type")
        stype = SourceDtoMapper.parse_source_type(raw_stype, is_local or False) if raw_stype else None

        update_fn = getattr(self.app_state, "update_data_source", None)
        updated_src = (
            update_fn(
                source_id=source_id,
                name=name,
                is_local=is_local,
                source_type=stype,
                connection_string=conn,
            )
            if callable(update_fn)
            else None
        )

        if not updated_src:
            get_src_fn = getattr(self.app_state, "get_data_source", None)
            existing = get_src_fn(source_id) if callable(get_src_fn) else None
            if not existing:
                raise ValueError(f"Sensor com ID '{source_id}' não encontrado.")

        sources_mgr = getattr(self.app_state, "sources", None)
        location_str = None
        if "location" in payload or "associated_element" in payload:
            loc = payload.get("location") if "location" in payload else payload.get("associated_element")
            location_str = str(loc).strip() if loc else ""
            if sources_mgr is not None:
                sources_mgr.associate(source_id, location_str)
            sig = getattr(self.app_state, "data_association_changed", None)
            if sig is not None:
                sig.emit(source_id, location_str)
        elif sources_mgr is not None:
            location_str = sources_mgr.get_element_for_source(source_id)

        if self.audit_logger:
            src_name = updated_src.name if updated_src else (name or source_id)
            self.audit_logger.log_action(
                self._get_current_user(),
                "UPDATE_SENSOR",
                f"Sensor '{src_name}' ({source_id}) modificado com sucesso."
            )

        resolved_stype = (
            getattr(updated_src.source_type, "value", None)
            if updated_src is not None
            else (stype.value if stype else None)
        )
        return {
            "success": True,
            "id": source_id,
            "name": updated_src.name if updated_src else name,
            "is_local": updated_src.is_local if updated_src else is_local,
            "source_type": resolved_stype,
            "associated_element": location_str,
        }

    def handle_associate_source(self, msg: IpcMessage) -> Dict[str, Any]:
        source_id = msg.payload.get("source_id")
        element_id = msg.payload.get("element_id")
        if source_id and element_id:
            sources_mgr = getattr(self.app_state, "sources", None)
            if sources_mgr is not None:
                sources_mgr.associate(source_id, element_id)
            sig = getattr(self.app_state, "data_association_changed", None)
            if sig is not None:
                sig.emit(source_id, element_id)
        elif source_id:
            enter_fn = getattr(self.app_state, "enter_association_mode", None) or getattr(
                self.app_state, "set_selected_source_for_association", None
            )
            if callable(enter_fn):
                enter_fn(source_id)
        elif element_id:
            assoc_fn = getattr(self.app_state, "associate_selected_source_to_element", None)
            if callable(assoc_fn):
                assoc_fn(element_id)
        return {"source_id": source_id, "element_id": element_id, "success": True}

    def handle_toggle_origin(self, msg: IpcMessage) -> Dict[str, Any]:
        sid = msg.payload.get("source_id")
        toggle_fn = getattr(self.app_state, "toggle_source_origin", None)
        if sid and callable(toggle_fn):
            toggle_fn(sid)
        return {"source_id": sid}

    def handle_remove_source(self, msg: IpcMessage) -> Dict[str, Any]:
        SourceGuard.check_lockdown(self.security_manager)
        sid = msg.payload.get("source_id")
        remove_fn = getattr(self.app_state, "remove_data_source", None)
        if sid and callable(remove_fn):
            remove_fn(sid)
            if self.audit_logger:
                self.audit_logger.log_action(
                    self._get_current_user(),
                    "REMOVE_SENSOR",
                    f"Sensor removido: {sid}"
                )
            if self.telemetry_service:
                self.telemetry_service.report_incident(
                    "SOFTWARE",
                    "WARNING",
                    f"Sensor removido do sistema: {sid}"
                )
        return {"source_id": sid}

    def handle_preview_batch_sources(self, msg: IpcMessage) -> Dict[str, Any]:
        csv_content = msg.payload.get("csv_content", "")
        file_path = msg.payload.get("file_path")
        if not csv_content and file_path and os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    csv_content = f.read()
            except Exception as e:
                return {
                    "total": 0,
                    "valid_count": 0,
                    "error_count": 1,
                    "parse_errors": [f"Erro ao ler arquivo CSV: {str(e)}"],
                    "items": [],
                }

        topology = getattr(self.app_state, "topology", None)
        return SensorBatchService.preview_manifest(csv_content, topology)

    def handle_import_batch_sources(self, msg: IpcMessage) -> Dict[str, Any]:
        SourceGuard.check_lockdown(self.security_manager)
        csv_content = msg.payload.get("csv_content", "")
        file_path = msg.payload.get("file_path")
        if not csv_content and file_path and os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    csv_content = f.read()
            except Exception as e:
                return {
                    "success": False,
                    "imported_count": 0,
                    "errors": [f"Erro ao ler arquivo CSV: {str(e)}"],
                    "sensors": [],
                }

        host = msg.payload.get("host")
        port = msg.payload.get("port")

        records, _ = SensorBatchService.parse_csv_records(csv_content)
        has_local = any(r.get("type") == "local" for r in records)

        if has_local:
            try:
                SourceGuard.ensure_local_sensor_prerequisites(True)
            except ValueError as e:
                return {
                    "success": False,
                    "imported_count": 0,
                    "errors": [str(e)],
                    "sensors": [],
                }

        result = SensorBatchService.import_manifest(
            csv_content=csv_content,
            app_state=self.app_state,
            host=host,
            port=port,
        )

        if result.get("success") and self.audit_logger:
            self.audit_logger.log_action(
                self._get_current_user(),
                "BATCH_IMPORT_SENSORS",
                f"Importação em lote: {result.get('imported_count', 0)} sensores locais provisionados via CSV."
            )

        return result
