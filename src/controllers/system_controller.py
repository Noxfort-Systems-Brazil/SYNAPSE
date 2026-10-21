# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Dict, Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal

# --- Domain & Managers ---
from src.domain.app_state import AppState
from src.managers.storage_manager import StorageManager
from src.controllers.phase_signal_connector import PhaseSignalConnector


class SystemController(QObject):
    """
    The Master Operations Controller.
    
    Refactored V39 (SOLID Architecture):
    - [SRP] OS folder scaffolding delegated to StorageManager, wiring to PhaseSignalConnector.
    - [DIP] Receives initialized `FenixService` and `phases` dictionary via Injection.
    - [OCP] Uses a flexible State Machine ruleset instead of hardcoded if/else rules.
    """

    # --- TELEMETRY SIGNALS (Aggregated) ---
    log_message = pyqtSignal(str)
    status_message = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    # --- LIFECYCLE SIGNALS ---
    optimization_finished = pyqtSignal()
    bootstrap_finished = pyqtSignal()
    online_system_started = pyqtSignal()
    online_system_stopped = pyqtSignal()
    
    # --- DATA STREAMS (Proxied from Runtime) ---
    engine_data_processed = pyqtSignal(dict)
    engine_global_results = pyqtSignal(dict)
    kinetic_data_ready = pyqtSignal(dict)
    
    # --- ADVANCED STREAMS ---
    audit_update = pyqtSignal(bool, float, float, list)
    linguist_update = pyqtSignal(str, str, float)
    drift_update = pyqtSignal(str, dict)
    xai_result_received = pyqtSignal(dict)

    # --- COMMANDS ---
    cmd_process_data = pyqtSignal(str, object)
    cmd_run_cycle = pyqtSignal()
    cmd_update_model = pyqtSignal(str)
    
    cmd_explain_buffer = pyqtSignal()
    cmd_explain_local = pyqtSignal(str)
    cmd_explain_global = pyqtSignal()

    def __init__(self, app_state: AppState, storage_manager: StorageManager, phases: Dict[str, Any], fenix_service: Any):
        super().__init__()
        self.app_state = app_state
        self.storage = storage_manager
        
        # [DIP] Injected Dependencies
        self.fenix_service = fenix_service
        self.phases = phases
        self._completed_phases = set()
        self._on_demand_xai_manager: Optional[Any] = None
        self._on_demand_xai_worker: Optional[Any] = None

        # Connect Storage
        if self.storage:
            try:
                self.storage.connect()
            except Exception as e:
                print(f"[SystemController] Storage Connection Warning: {e}")

        self._connect_fenix_signals()
        
        # --- Wire Up Injected Phases ---
        if "optimization" in self.phases:
            self._connect_optimization_phase(self.phases["optimization"])
        if "bootstrap" in self.phases:
            self._connect_bootstrap_phase(self.phases["bootstrap"])
        if "runtime" in self.phases:
            self._connect_runtime_phase(self.phases["runtime"])
            self._connect_commands(self.phases["runtime"])
        
        self.log_message.emit("[SystemController] 🟢 Initialized (V39 SOLID Final).")

    def _connect_fenix_signals(self):
        PhaseSignalConnector.connect_fenix_signals(self, self.fenix_service)

    def _on_fenix_finished(self, success, msg):
        status_icon = '✅' if success else '❌'
        self.log_message.emit(f"[FENIX] {status_icon} {msg}")

    # =========================================================================
    # PHASE WIRING
    # =========================================================================

    def _connect_optimization_phase(self, phase_obj):
        PhaseSignalConnector.connect_optimization_phase(self, phase_obj)

    def _connect_bootstrap_phase(self, phase_obj):
        PhaseSignalConnector.connect_bootstrap_phase(self, phase_obj)

    def _connect_runtime_phase(self, phase_obj):
        PhaseSignalConnector.connect_runtime_phase(self, phase_obj)

    def _connect_commands(self, runtime_obj):
        PhaseSignalConnector.connect_commands(self, runtime_obj)

    def _get_on_demand_xai(self):
        if self._on_demand_xai_manager is None:
            from src.workers.xai_worker import XAIWorker
            from src.managers.xai_manager import XAIManager
            from src.services.semantic_enricher import SemanticEnricher
            worker = XAIWorker(model_config={"feature_dim": 1})
            worker.result_ready.connect(self.xai_result_received.emit)
            enricher = SemanticEnricher(self.app_state)
            self._on_demand_xai_manager = XAIManager(worker, enricher)
            self._on_demand_xai_worker = worker
        return self._on_demand_xai_manager

    def _handle_explain_buffer_cmd(self, runtime_obj):
        PhaseSignalConnector.handle_explain_buffer(self, runtime_obj)

    def _handle_explain_local_cmd(self, runtime_obj, sid: str):
        PhaseSignalConnector.handle_explain_local(self, runtime_obj, sid)

    def _handle_explain_global_cmd(self, runtime_obj):
        PhaseSignalConnector.handle_explain_global(self, runtime_obj)

    # =========================================================================
    # INTERNAL HANDLERS (Dynamic State Completion & Auto-Progression)
    # =========================================================================

    def detect_completed_phases(self) -> set:
        """Inspects disk artifacts via StorageManager to detect previously completed phases."""
        completed = set()
        if self.storage:
            p0_fn = getattr(self.storage, "has_phase0_artifacts", None)
            p1_fn = getattr(self.storage, "has_phase1_artifacts", None)
            if callable(p0_fn) and p0_fn():
                completed.add("optimization")
            if callable(p1_fn) and p1_fn():
                if "optimization" in completed:
                    completed.add("bootstrap")
        return completed

    def sync_completed_phases(self) -> str:
        """
        Synchronizes internal state with persisted artifacts and returns the recommended active phase.
        Returns: 'runtime', 'bootstrap', or 'optimization'.
        """
        detected = self.detect_completed_phases()
        self._completed_phases.update(detected)

        if "optimization" in self._completed_phases and "bootstrap" in self._completed_phases:
            return "runtime"
        elif "optimization" in self._completed_phases:
            return "bootstrap"
        return "optimization"

    def _on_optimization_finished(self):
        self._completed_phases.add("optimization")
        self.log_message.emit("🔒 Security: Phase 0 (Optimization) Verified.")

        p1_fn = getattr(self.storage, "has_phase1_artifacts", None) if self.storage else None
        if callable(p1_fn) and p1_fn():
            self._completed_phases.add("bootstrap")
            self.log_message.emit("⚡ Auto-Progression: Phase 1 (Bootstrap) artifacts already present. Skipping directly to Phase 2 (Live Operation).")
            self.status_message.emit("Phase 0 & 1 Complete. Ready for Phase 2 (Live Operation).")
            self.bootstrap_finished.emit()
        else:
            self.status_message.emit("Phase 0 Complete. Ready for Phase 1.")
            self.optimization_finished.emit()

    def _on_bootstrap_finished(self):
        self._completed_phases.add("bootstrap")
        self.log_message.emit("🔒 Security: Phase 1 (Bootstrap) Verified.")
        self.status_message.emit("Phase 1 Complete. Ready for Phase 2.")
        self.bootstrap_finished.emit()

    # =========================================================================
    # PUBLIC API (State Machine)
    # =========================================================================

    def _execute_phase(self, phase_name: str, prerequisites: list) -> bool:
        """
        Generic State Machine executor. Evaluates rules before starting a mapped phase.
        Automatically syncs with disk artifacts before verifying prerequisites.
        """
        self.sync_completed_phases()

        for req in prerequisites:
            if req not in self._completed_phases:
                msg = f"⛔ Phase '{req}' must be completed before starting '{phase_name}'."
                self.log_message.emit(msg)
                self.error_occurred.emit(msg)
                return False
                
        if phase_name in self.phases:
            result = self.phases[phase_name].start()
            return result if isinstance(result, bool) else True
        else:
            self.error_occurred.emit(f"⛔ Required system phase '{phase_name}' is not registered.")
            return False

    def _halt_phase(self, phase_name: str):
        if phase_name in self.phases:
            self.phases[phase_name].stop()

    def start_optimization(self):
        return self._execute_phase("optimization", prerequisites=[])

    def stop_optimization(self):
        self._halt_phase("optimization")

    def start_offline_bootstrap(self):
        return self._execute_phase("bootstrap", prerequisites=["optimization"])

    def stop_offline_bootstrap(self):
        self._halt_phase("bootstrap")

    def start_online_operation(self):
        return self._execute_phase("runtime", prerequisites=["optimization", "bootstrap"])

    def stop_online_operation(self):
        self._halt_phase("runtime")
