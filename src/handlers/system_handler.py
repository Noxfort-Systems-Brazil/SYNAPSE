# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
System Lifecycle & Diagnostics Command Handler (SOLID: SRP & DIP).

Translates IPC actions related to application lifecycle, online/offline pipeline runs,
and explainability (XAI) commands to the underlying MainController / SystemController.
"""

from typing import Any, Callable, Dict, Optional

from src.ipc.ipc_protocol import IpcMessage
from src.ipc.command_router import Responder
from src.utils.logging_setup import get_logger


class SystemCommandHandler:
    """Handles system lifecycle, flow controls, and diagnostic actions."""

    def __init__(
        self,
        controller: Any,
        on_shutdown: Optional[Callable[[], None]] = None,
        security_manager: Optional[Any] = None,
        audit_logger: Optional[Any] = None,
        report_service: Optional[Any] = None,
    ):
        self.controller = controller
        self.on_shutdown = on_shutdown
        self.security_manager = security_manager
        self.audit_logger = audit_logger
        self.report_service = report_service
        self.logger = get_logger("SystemCommandHandler")
        self._connected = False

    def _get_current_user(self) -> str:
        user = getattr(self.security_manager, "last_auth_user", None) if self.security_manager else None
        return user or "SYSTEM"

    def handle_get_system_status(self, msg: IpcMessage) -> Dict[str, Any]:
        recommended_phase = "IDLE_OPTIMIZATION"
        completed_phases = []
        sys_ctrl = getattr(self.controller, "system", None)
        sync_fn = getattr(sys_ctrl, "sync_completed_phases", None) if sys_ctrl else None
        if callable(sync_fn):
            stage = sync_fn()
            completed = getattr(sys_ctrl, "_completed_phases", set())
            completed_phases = list(completed)
            if stage == "runtime":
                recommended_phase = "IDLE_ONLINE"
            elif stage == "bootstrap":
                recommended_phase = "IDLE_OFFLINE"
            else:
                recommended_phase = "IDLE_OPTIMIZATION"

        has_dataset = False
        storage = getattr(self.controller, "storage", None)
        has_ds_fn = getattr(storage, "has_historical_dataset", None) if storage else None
        if callable(has_ds_fn):
            has_dataset = has_ds_fn()
        elif storage:
            base_dir = getattr(storage, "base_dir", None)
            glob_fn = getattr(base_dir, "glob", None)
            if callable(glob_fn):
                has_dataset = len(list(glob_fn("*.parquet"))) > 0

        return {
            "status": "ok",
            "phase": recommended_phase,
            "completed_phases": completed_phases,
            "has_dataset": has_dataset,
        }

    def handle_ping(self, msg: IpcMessage) -> Dict[str, Any]:
        if not self._connected:
            self._connected = True
            self.logger.info("🟢 [IPC STATUS] CONECTADO: Frontend Desktop (Tauri/React) conectado ao backend Python.")
        status_info = self.handle_get_system_status(msg)
        status_info["app"] = "SYNAPSE v2.0"
        return status_info

    def handle_start_optimization(self, msg: IpcMessage) -> Dict[str, Any]:
        if self.security_manager and self.security_manager.is_lockdown():
            raise RuntimeError("Operação bloqueada. O sistema está em estado de LOCKDOWN.")
        res = self.controller.start_optimization_flow()
        if self.audit_logger:
            self.audit_logger.log_action(self._get_current_user(), "START_OPTIMIZATION", "Início do fluxo de Otimização de Topologia")
        return {"started": res}

    def handle_stop_optimization(self, msg: IpcMessage) -> Dict[str, Any]:
        sys_ctrl = getattr(self.controller, "system", None)
        if sys_ctrl is not None:
            sys_ctrl.stop_optimization()
        if self.audit_logger:
            self.audit_logger.log_action(self._get_current_user(), "STOP_OPTIMIZATION", "Interrupção da Otimização de Topologia")
        return {"stopped": True}

    def handle_start_offline_bootstrap(self, msg: IpcMessage) -> Dict[str, Any]:
        if self.security_manager and self.security_manager.is_lockdown():
            raise RuntimeError("Operação bloqueada. O sistema está em estado de LOCKDOWN.")
        sys_ctrl = getattr(self.controller, "system", None)
        if sys_ctrl is not None:
            sys_ctrl.start_offline_bootstrap()
        if self.audit_logger:
            self.audit_logger.log_action(self._get_current_user(), "START_OFFLINE_BOOTSTRAP", "Início do Bootstrap Offline dos modelos MEH")
        return {"started": True}

    def handle_stop_offline_bootstrap(self, msg: IpcMessage) -> Dict[str, Any]:
        sys_ctrl = getattr(self.controller, "system", None)
        if sys_ctrl is not None:
            sys_ctrl.stop_offline_bootstrap()
        if self.audit_logger:
            self.audit_logger.log_action(self._get_current_user(), "STOP_OFFLINE_BOOTSTRAP", "Interrupção do Bootstrap Offline")
        return {"stopped": True}

    def handle_start_online_operation(self, msg: IpcMessage) -> Dict[str, Any]:
        if self.security_manager and self.security_manager.is_lockdown():
            raise RuntimeError("Operação bloqueada. O sistema está em estado de LOCKDOWN.")
        sys_ctrl = getattr(self.controller, "system", None)
        if sys_ctrl is not None:
            sys_ctrl.start_online_operation()
        if self.audit_logger:
            self.audit_logger.log_action(self._get_current_user(), "START_ONLINE_OPERATION", "Início da Operação Online em Tempo Real (HFT)")
        return {"started": True}

    def handle_stop_online_operation(self, msg: IpcMessage) -> Dict[str, Any]:
        sys_ctrl = getattr(self.controller, "system", None)
        if sys_ctrl is not None:
            sys_ctrl.stop_online_operation()
        if self.audit_logger:
            self.audit_logger.log_action(self._get_current_user(), "STOP_ONLINE_OPERATION", "Interrupção da Operação Online")
        return {"stopped": True}

    def handle_explain_buffer(self, msg: IpcMessage) -> Dict[str, Any]:
        sys_ctrl = getattr(self.controller, "system", None)
        sig = getattr(sys_ctrl, "cmd_explain_buffer", None) if sys_ctrl else None
        if sig is not None:
            sig.emit()
        return {"requested": "buffer"}

    def handle_explain_local(self, msg: IpcMessage) -> Dict[str, Any]:
        node_id = msg.payload.get("node_id", "")
        sys_ctrl = getattr(self.controller, "system", None)
        sig = getattr(sys_ctrl, "cmd_explain_local", None) if sys_ctrl else None
        if sig is not None:
            sig.emit(node_id)
        return {"requested": "local", "node_id": node_id}

    def handle_explain_global(self, msg: IpcMessage) -> Dict[str, Any]:
        sys_ctrl = getattr(self.controller, "system", None)
        sig = getattr(sys_ctrl, "cmd_explain_global", None) if sys_ctrl else None
        if sig is not None:
            sig.emit()
        return {"requested": "global"}

    def handle_hot_swap_model(self, msg: IpcMessage) -> Dict[str, Any]:
        payload = msg.payload or {}
        model_path = payload.get("model_path", "")
        self.logger.info(f"🔄 [IPC] Hot-swap requested for model checkpoint: {model_path}")
        fenix = getattr(self.controller, "fenix_service", None)
        sys_ctrl = getattr(self.controller, "system", None)
        if fenix is not None:
            fenix.request_model_hot_swap.emit(model_path)
        elif sys_ctrl is not None:
            sig = getattr(sys_ctrl, "request_model_hot_swap", None)
            if sig is not None:
                sig.emit(model_path)
        return {"hot_swap_requested": True, "model_path": model_path}

    def handle_get_process_health(self, msg: IpcMessage) -> Dict[str, Any]:
        import os
        return {
            "status": "healthy",
            "pid": os.getpid(),
            "supervised": os.environ.get("SYNAPSE_SUPERVISED") == "1",
        }

    def handle_reset_workspace(self, msg: IpcMessage) -> Dict[str, Any]:
        """Completely wipes in-memory AppState, disk sources.json, datalake, and PostgreSQL vault."""
        self.logger.info("🧹 [SystemCommandHandler] Solicitando reset completo do espaço de trabalho...")

        # 1. Reset in-memory AppState if available
        app_state = getattr(self.controller, "app_state", None)
        clear_fn = getattr(app_state, "clear", None) if app_state else None
        if callable(clear_fn):
            clear_fn()

        # 2. Reset project controller if available
        project_ctrl = getattr(self.controller, "project_ctrl", None)
        new_proj_fn = getattr(project_ctrl, "create_new_project", None) if project_ctrl else None
        if callable(new_proj_fn):
            try:
                project_ctrl.create_new_project()
            except Exception as pe:
                self.logger.warning(f"Aviso ao chamar create_new_project: {pe}")

        # 3. Reset disk files (sources.json, datalake, checkpoints)
        try:
            import json
            from pathlib import Path
            from src.storage.path_scaffolder import PathScaffolder
            scaffolder = PathScaffolder()
            synapse_dir = scaffolder.project_root
            sources_json = scaffolder.config_dir / "sources.json"
            if sources_json.parent.exists():
                with open(sources_json, "w", encoding="utf-8") as f:
                    json.dump({"map_path": None, "sources": [], "associations": {}}, f, indent=2)
            for folder in [scaffolder.base_dir, scaffolder.golden_dir, scaffolder.checkpoint_dir, scaffolder.data_config_dir]:
                if folder.exists():
                    for item in folder.glob("*"):
                        if item.is_file():
                            try:
                                item.unlink()
                            except Exception:
                                pass
        except Exception as fe:
            self.logger.warning(f"Aviso ao limpar arquivos locais: {fe}")

        # 4. Clear database schema tables
        try:
            from src.database.db_engine import DatabaseEngine
            engine = DatabaseEngine()
            conn = engine.get_connection()
            if conn:
                cursor = conn.cursor()
                schema = getattr(engine, "schema", "schema_synapse") or "schema_synapse"
                for t in ["cloud_file_vault", "sensor_dictionary", "synapse_sensor_telemetry_raw", "synapse_sensor_hourly_summary", "synapse_golden_history", "audit_physics_episodes", "operation_sessions"]:
                    try:
                        cursor.execute(f"DELETE FROM {schema}.{t};")
                    except Exception:
                        pass
                conn.commit()
                conn.close()
        except Exception as de:
            self.logger.warning(f"Aviso ao limpar tabelas do banco: {de}")

        if self.audit_logger:
            self.audit_logger.log_action(
                self._get_current_user(),
                "RESET_WORKSPACE",
                "Espaço de trabalho, mapa e fontes de dados resetados para o estado inicial zero.",
            )

        return {
            "success": True,
            "message": "Espaço de trabalho zerado com sucesso. Nenhum mapa ou sensor carregado.",
        }

    def handle_shutdown(self, msg: IpcMessage, responder: Responder) -> None:
        responder(True, {"shutting_down": True})
        if self.on_shutdown:
            self.on_shutdown()

