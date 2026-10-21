# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
High-Capacity Go Ingestion Gateway Adapter (SOLID: SRP, OCP, DIP).

Connects the Zero Trust Ingestion Hub to the high-concurrency Go ingestion gateway
communicating exclusively through OS Anonymous Pipes (STDIN/STDOUT).
Zero filesystem socket artifacts, zero internal network loopback ports.
"""

from typing import Any, Dict, Optional, Tuple

from src.adapters.adaptive_poller import AdaptivePollingController
from src.adapters.base_adapter import BaseIngestionAdapter
from src.domain.entities import DataSource
from src.go.subprocess_transport import GoSubprocessTransport
from src.interfaces.gateway_transport import IGatewayTransport


class GoPushAdapter(BaseIngestionAdapter):
    """
    Unified Ingestion Transport Adapter powered by the compiled Go Gateway daemon.
    Communicates strictly through OS Anonymous Pipes (STDIN/STDOUT).
    Designed for massive concurrent edge AI cameras, radar stations, and IoT nodes.
    """

    def __init__(
        self,
        adapter_id: str = "go_ingestion_gateway",
        bin_path: Optional[str] = None,
        transport: Optional[IGatewayTransport] = None,
        adaptive_controller: Optional[AdaptivePollingController] = None,
    ):
        super().__init__(adapter_id=adapter_id, transport_name="Go-Gateway")
        self.transport: IGatewayTransport = transport or GoSubprocessTransport(bin_path=bin_path)
        self.adaptive_controller: AdaptivePollingController = (
            adaptive_controller or AdaptivePollingController()
        )
        self._registered_poll_sources: Dict[str, Tuple[str, float]] = {}
        self._registered_local_sources: set = set()

    def _do_start(self) -> None:
        """Launches the Go gateway subprocess and binds OS anonymous pipes."""
        success = self.transport.start(on_packet_received=self._on_transport_packet)
        if not success:
            self._logger.warning(
                "[GoPushAdapter] Could not boot Go binary. Subprocess transport inactive."
            )
            return

        # 1. Replay all registered polling targets registered prior to transport boot
        for src_id, (conn_str, interval) in list(self._registered_poll_sources.items()):
            self.transport.register_poll_source(src_id, conn_str, interval_sec=interval)
            self._logger.info(
                f"🌐 [GoPushAdapter] Replayed polling target '{src_id}' -> {conn_str} after transport boot."
            )

        # 2. Check persistent DuckDNS configuration and activate if enabled
        try:
            from src.database.db_settings_manager import DatabaseSettingsManager
            duck_cfg = DatabaseSettingsManager().load_duckdns_settings()
            if duck_cfg.get("enabled", False) and duck_cfg.get("domain"):
                domain = str(duck_cfg.get("domain", "")).strip()
                token = str(duck_cfg.get("token", "")).strip()
                port = int(duck_cfg.get("port", 8081))
                https_port = int(duck_cfg.get("https_port", 443))
                caddy_enabled = bool(duck_cfg.get("caddy_enabled", True))
                send_cmd_fn = getattr(self.transport, "send_command", None)
                if callable(send_cmd_fn):
                    send_cmd_fn({
                        "cmd": "SET_DUCKDNS",
                        "domain": domain,
                        "token": token,
                        "port": str(port),
                        "https_port": https_port,
                        "caddy_enabled": caddy_enabled,
                        "enabled": True,
                    })
        except Exception as e:
            self._logger.warning(f"[GoPushAdapter] Could not auto-sync DuckDNS on start: {e}")

    def _do_stop(self) -> None:
        """Signals shutdown to the Go gateway subprocess (which terminates Caddy automatically)."""
        self.transport.stop()

    def _on_transport_packet(
        self, source_id: str, payload: Any, metadata: Optional[Dict[str, Any]]
    ) -> None:
        """Callback invoked when a packet arrives from Go over STDOUT pipe."""
        # Dynamic Polling Rate evaluation for external polling targets
        if source_id in self._registered_poll_sources:
            conn_str, curr_interval = self._registered_poll_sources[source_id]
            new_interval, changed = self.adaptive_controller.evaluate_packet(source_id, payload)
            if changed:
                self._registered_poll_sources[source_id] = (conn_str, new_interval)
                self.transport.register_poll_source(source_id, conn_str, interval_sec=new_interval)

        combined_meta = {
            "transport": self.transport_name,
        }
        if metadata:
            combined_meta.update(metadata)

        self.emit_packet(
            source_id=source_id,
            payload=payload,
            metadata=combined_meta,
        )

    def register_source(self, source: DataSource) -> None:
        """Registers a data source with this unified Go adapter (Push or Poller)."""
        # If it's an external HTTP/HTTPS URL (global), register as a concurrent polling target in Go daemon
        if not source.is_local and source.connection_string and isinstance(source.connection_string, str):
            if source.connection_string.startswith("http://") or source.connection_string.startswith("https://"):
                is_quarantine = (getattr(source.status, "value", str(source.status)) == "Quarantine")
                interval = self.adaptive_controller.register_source(source.id, is_quarantine=is_quarantine)
                curr_reg = self._registered_poll_sources.get(source.id)
                if curr_reg == (source.connection_string, interval):
                    return  # Already registered with identical parameters; avoid redundant IPC & log spam

                self._registered_poll_sources[source.id] = (source.connection_string, interval)
                self.transport.register_poll_source(source.id, source.connection_string, interval_sec=interval)
                self._logger.info(
                    f"🌐 [GoPushAdapter] Delegated polling target '{source.name}' ({source.id}) "
                    f"-> {source.connection_string} to Go Poller engine (interval={interval:.1f}s)."
                )
        else:
            if source.id in self._registered_local_sources:
                return  # Local source already registered; avoid redundant debug log spam
            self._registered_local_sources.add(source.id)
            self._logger.debug(f"[GoPushAdapter] Source registered: {source.id}")

    def unregister_source(self, source_id: str) -> None:
        """Unregisters a data source."""
        self._logger.debug(f"[GoPushAdapter] Source unregistered: {source_id}")
        self._registered_poll_sources.pop(source_id, None)
        self._registered_local_sources.discard(source_id)
        self.adaptive_controller.unregister_source(source_id)
        self.transport.unregister_poll_source(source_id)


# Semantic alias reflecting unified Push, Poller, and MQTT capabilities
GoIngestionAdapter = GoPushAdapter
