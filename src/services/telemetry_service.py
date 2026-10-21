# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Telemetry Service (SOLID: SRP & DIP).

Decouples telemetry lifecycle, MQTT reporting and shutdown flushes from controllers.
Implements ITelemetryService interface.
"""

import time
import logging
from typing import Optional

from PyQt6.QtCore import QCoreApplication
from src.infrastructure.monitor_client import MonitorClient
from src.interfaces.controllers import ITelemetryService

logger = logging.getLogger(__name__)


class TelemetryService(ITelemetryService):
    """
    Manages telemetry connections, incident reporting and graceful shutdown flushes.
    """

    def __init__(self, monitor_client: Optional[MonitorClient] = None):
        self._monitor_client: Optional[MonitorClient] = monitor_client
        self._ingestion_counts: dict[str, int] = {}
        if self._monitor_client is None:
            self._auto_load_from_settings()

    def record_ingestion(self, source_id: str) -> None:
        """Records a packet ingestion event for a validated source."""
        if not source_id:
            return
        self._ingestion_counts[source_id] = self._ingestion_counts.get(source_id, 0) + 1

    def _auto_load_from_settings(self) -> None:
        """Loads persistent telemetry settings on service initialization."""
        try:
            from src.database.db_settings_manager import DatabaseSettingsManager
            settings_mgr = DatabaseSettingsManager()
            cfg = settings_mgr.load_telemetry_settings()
            if cfg.get("connected"):
                ip = cfg.get("ip") or cfg.get("host") or "localhost"
                port = int(cfg.get("port", 1883))
                self.init_telemetry(enabled=True, host=ip, port=port)
        except Exception as e:
            logger.debug(f"[TelemetryService] Could not auto-load telemetry settings: {e}")

    @property
    def monitor_client(self) -> Optional[MonitorClient]:
        return self._monitor_client

    @property
    def enabled(self) -> bool:
        return self._monitor_client.enabled if self._monitor_client else False

    def init_telemetry(self, enabled: bool, host: str, port: int = 1883) -> None:
        """Initializes or restarts the background MonitorClient (HTTP or MQTT)."""
        if self._monitor_client:
            try:
                self._monitor_client.stop()
            except Exception as e:
                logger.warning(f"[TelemetryService] Failed stopping previous monitor client: {e}")

        self._monitor_client = MonitorClient(host=host, port=port, enabled=enabled)
        mode = "HTTP" if self._monitor_client.is_http else "MQTT"
        logger.info(f"[TelemetryService] Telemetry configured (mode={mode}, enabled={enabled}, target={host}:{port})")

    def reconfigure_telemetry(self, enabled: bool, host: str, port: int) -> None:
        """Reconfigures telemetry settings."""
        self.init_telemetry(enabled, host, port)

    def report_error(self, message: str) -> None:
        """Dispatches a critical software incident through the monitor client."""
        self.report_incident(category="SOFTWARE", level="CRITICAL", message=message)

    def report_incident(self, category: str, level: str, message: str) -> None:
        """Dispatches an incident report through the monitor client."""
        if self._monitor_client and self._monitor_client.enabled:
            try:
                self._monitor_client.report_incident(category=category, level=level, message=message)
            except Exception as e:
                logger.error(f"[TelemetryService] Error reporting incident: {e}")

    def report_shutdown(self) -> None:
        """
        Dispatches a shutdown event and waits briefly to allow the MQTT queue to flush.
        """
        if self._monitor_client and self._monitor_client.enabled:
            try:
                msg = QCoreApplication.translate("MainController", "System Shutdown Initiated")
                self._monitor_client.report_incident(category="SOFTWARE", level="CRITICAL", message=msg)
                # Blocking delay ensuring MQTT queue flush before process termination
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"[TelemetryService] Error during shutdown telemetry report: {e}")
