# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Any


class PhaseSignalConnector:
    """Wires up PyQt signals and external command routing for system controller phases."""

    @staticmethod
    def connect_fenix_signals(controller: Any, fenix_service: Any) -> None:
        """Bridges FENIX service signals to UI log/status."""
        if fenix_service is None:
            return
        fenix_service.cycle_started.connect(lambda msg: controller.log_message.emit(f"[FENIX] 🔥 {msg}"))
        fenix_service.cycle_finished.connect(controller._on_fenix_finished)
        fenix_service.progress_update.connect(lambda msg, pct: controller.status_message.emit(f"FENIX: {msg} ({pct}%)"))

    @staticmethod
    def connect_optimization_phase(controller: Any, phase_obj: Any) -> None:
        phase_obj.log_message.connect(controller.log_message)
        phase_obj.error_occurred.connect(controller.error_occurred)
        phase_obj.optimization_finished.connect(controller._on_optimization_finished)

    @staticmethod
    def connect_bootstrap_phase(controller: Any, phase_obj: Any) -> None:
        phase_obj.log_message.connect(controller.log_message)
        phase_obj.bootstrap_finished.connect(controller._on_bootstrap_finished)

    @staticmethod
    def connect_runtime_phase(controller: Any, phase_obj: Any) -> None:
        # Telemetry
        phase_obj.log_message.connect(controller.log_message)
        phase_obj.status_message.connect(controller.status_message)
        phase_obj.error_occurred.connect(controller.error_occurred)
        
        # Lifecycle
        phase_obj.system_started.connect(controller.online_system_started)
        phase_obj.system_stopped.connect(controller.online_system_stopped)
        
        # Data Streams
        phase_obj.engine_data_processed.connect(controller.engine_data_processed)
        phase_obj.engine_global_results.connect(controller.engine_global_results)
        phase_obj.kinetic_data_ready.connect(controller.kinetic_data_ready)
        phase_obj.audit_update.connect(controller.audit_update)
        phase_obj.linguist_update.connect(controller.linguist_update)
        phase_obj.drift_update.connect(controller.drift_update)
        phase_obj.xai_result_received.connect(controller.xai_result_received)

    @staticmethod
    def connect_commands(controller: Any, runtime_obj: Any) -> None:
        """Routes external commands (e.g. from UI) to the Runtime Phase with On-Demand fallback."""
        controller.cmd_process_data.connect(lambda t, p: runtime_obj.handle_command("process_data", p))
        controller.cmd_run_cycle.connect(lambda: runtime_obj.handle_command("run_cycle"))
        controller.cmd_update_model.connect(lambda p: runtime_obj.handle_command("update_model", p))
        controller.cmd_explain_buffer.connect(lambda: controller._handle_explain_buffer_cmd(runtime_obj))
        controller.cmd_explain_local.connect(lambda pid: controller._handle_explain_local_cmd(runtime_obj, pid))
        controller.cmd_explain_global.connect(lambda: controller._handle_explain_global_cmd(runtime_obj))

    @staticmethod
    def handle_explain_buffer(controller: Any, runtime_obj: Any) -> None:
        if runtime_obj and getattr(runtime_obj, "launcher", None) and getattr(runtime_obj.launcher, "_engine_worker", None):
            runtime_obj.handle_command("explain_buffer")
        else:
            xai = controller._get_on_demand_xai()
            get_nodes_fn = getattr(controller.app_state, "get_all_nodes", None)
            nodes = [n.id for n in get_nodes_fn()] if callable(get_nodes_fn) else []
            xai.process_buffer_strategy(nodes)

    @staticmethod
    def handle_explain_local(controller: Any, runtime_obj: Any, sid: str) -> None:
        resolved_sid = sid
        get_nodes_fn = getattr(controller.app_state, "get_all_nodes", None)
        if not resolved_sid and callable(get_nodes_fn):
            all_nodes = get_nodes_fn()
            if all_nodes:
                resolved_sid = all_nodes[0].id
        get_sources_fn = getattr(controller.app_state, "get_all_data_sources", None)
        if not resolved_sid and callable(get_sources_fn):
            sources = get_sources_fn()
            if sources:
                resolved_sid = sources[0].id
        if not resolved_sid:
            resolved_sid = "Sensor_Principal"

        if runtime_obj and getattr(runtime_obj, "launcher", None) and getattr(runtime_obj.launcher, "_engine_worker", None):
            runtime_obj.handle_command("explain_local", resolved_sid)
        else:
            xai = controller._get_on_demand_xai()
            get_node_fn = getattr(controller.app_state, "get_node", None)
            node = get_node_fn(resolved_sid) if callable(get_node_fn) else None
            xai.explain_local(resolved_sid, node)

    @staticmethod
    def handle_explain_global(controller: Any, runtime_obj: Any) -> None:
        if runtime_obj and getattr(runtime_obj, "launcher", None) and getattr(runtime_obj.launcher, "_engine_worker", None):
            runtime_obj.handle_command("explain_global")
        else:
            xai = controller._get_on_demand_xai()
            nodes_dict = {}
            get_nodes_fn = getattr(controller.app_state, "get_all_nodes", None)
            if callable(get_nodes_fn):
                for n in get_nodes_fn():
                    nodes_dict[n.id] = n
            xai.explain_global(None, nodes_dict, seq_len=12)
