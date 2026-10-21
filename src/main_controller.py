# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Pure High-Level Orchestrator & Controller Aggregator (SOLID Architecture).

Adheres strictly to SOLID:
- [SRP] Zero direct object instantiation, zero telemetry logic, zero proxy signal repetition.
- [DIP] Injected with abstract protocols: ISystemController, IProjectController, IViewController, ITelemetryService.
- [ISP] Subsystems are segregated; callers connect directly to sub-controllers (system, project, view, telemetry).
- [OCP] Open to custom controllers, phases, and services injected via ControllerFactory.
"""

from typing import Optional, Any
from PyQt6.QtCore import QObject

from src.domain.app_state import AppState
from src.managers.storage_manager import StorageManager
from src.interfaces.controllers import (
    ISystemController,
    IProjectController,
    IViewController,
    ITelemetryService,
)


class MainController(QObject):
    """
    Pure High-Level Orchestrator & Controller Aggregator.
    Coordinates cross-cutting actions across System, Project, View, and Telemetry controllers.
    """

    def __init__(
        self,
        system_ctrl: ISystemController,
        project_ctrl: IProjectController,
        view_ctrl: IViewController,
        telemetry_service: ITelemetryService,
        app_state: AppState,
        storage: Optional[StorageManager] = None,
        fenix_service: Optional[Any] = None,
    ):
        super().__init__()
        self.system = system_ctrl
        self.project = project_ctrl
        self.view = view_ctrl
        self.telemetry = telemetry_service
        self.app_state = app_state
        self.storage = storage
        self.fenix_service = fenix_service

        # Backward compatibility aliases
        self.system_ctrl = self.system
        self.project_ctrl = self.project
        self.view_ctrl = self.view

        self._wire_internal_events()

    def _wire_internal_events(self):
        """Wires direct inter-controller notifications without intermediate proxy signals."""
        for src_obj, sig_name, dst_obj, slot_name in [
            (self.system, "log_message", self.view, "log"),
            (self.system, "status_message", self.view, "status"),
            (self.system, "error_occurred", self.view, "error_alert"),
            (self.system, "error_occurred", self.telemetry, "report_error"),
            (self.project, "log_message", self.view, "log"),
            (self.project, "error_occurred", self.view, "error_alert"),
            (self.project, "error_occurred", self.telemetry, "report_error"),
            (self.system, "online_system_started", self.view, "on_online_system_started"),
            (self.project, "project_loaded", self.view, "on_project_loaded"),
        ]:
            sig = getattr(src_obj, sig_name, None)
            slot = getattr(dst_obj, slot_name, None)
            if sig is not None and slot is not None:
                sig.connect(slot)

    # --- High-Level Orchestration Flows (Cross-Subsystem Operations) ---
    def start_optimization_flow(self) -> bool:
        """Orchestrates starting optimization and notifying the view layer."""
        started = self.system.start_optimization()
        on_opt_fn = getattr(self.view, "on_optimization_started", None)
        if started and callable(on_opt_fn):
            on_opt_fn()
        return bool(started)

    def shutdown(self):
        """Orchestrates graceful shutdown across all subsystems."""
        self.system.stop_online_operation()
        self.telemetry.report_shutdown()
