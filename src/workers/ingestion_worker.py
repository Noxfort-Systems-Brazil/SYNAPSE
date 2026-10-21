# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import time
from typing import Any, Dict, Optional

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

# --- Domain & Ingestion Adapters ---
from src.domain.app_state import AppState
from src.domain.entities import DataSource
from src.adapters.go_push_adapter import GoPushAdapter, GoIngestionAdapter
from src.adapters.ingestion_hub import IngestionHub
from src.go.subprocess_transport import GoSubprocessTransport
from src.pipeline.ingestion_pipeline import IngestionPipeline
from src.utils.logging_setup import get_logger

logger = get_logger("IngestionWorker")


class IngestionWorker(QObject):
    """
    Worker dedicated to Data Ingestion (The 'Mouth' of the System).
    
    Agnostic Architecture (SOLID & Hexagonal Ingestion):
    - [SRP] Coordinates ingestion lifecycle and data propagation to engine.
    - [OCP] Connects via IngestionHub to the high-concurrency Go ingestion gateway.
    - [LSP] Conforms structurally to Zero Trust pipeline contracts.
    - [ISP] Communicates via segregated interfaces (hub, pipeline, signal).
    - [DIP] Decoupled from transport specifics (network I/O isolated in Go daemon).
    """
    
    # Qt Signal emitted when valid, authenticated data passes the Zero Trust pipeline
    # Arguments: source_id (str), payload (dict/object)
    data_ready = pyqtSignal(str, object)

    def __init__(self, app_state: AppState, hub: Optional[IngestionHub] = None):
        super().__init__()
        self.app_state = app_state
        
        # 1. Zero Trust Pipeline (Pure Verification & Buffering)
        self.pipeline = IngestionPipeline(self.app_state)
        
        # 2. Agnostic Ingestion Hub
        self.hub = hub or IngestionHub(self.pipeline)
        
        # High-Throughput Go Ingestion Gateway (Zero-Port OS Anonymous Pipes)
        use_go = os.getenv("ENABLE_GO_GATEWAY", "1").lower() in ("1", "true", "yes")
        go_available = use_go and GoSubprocessTransport.ensure_compiled()

        self.go_adapter: Optional[GoPushAdapter] = None
        if go_available:
            self.go_adapter = GoPushAdapter(adapter_id="go_ingestion_gateway")
            self.hub.register_adapter(self.go_adapter)
            logger.info(
                "⚡ [IngestionWorker] Go High-Capacity Gateway active "
                "(OS Anonymous Pipes STDIN/STDOUT: Unified Ingestion Engine)."
            )
        else:
            logger.warning(
                "⚠️ [IngestionWorker] Go gateway binary not available or disabled."
            )

        # Backward-compatible property alias
        self.go_push_adapter = self.go_adapter

        # Track registered source IDs for bidirectional reconciliation
        self._known_source_ids: set = set()

        # Connect to AppState source removal signal if available
        removed_sig = getattr(self.app_state, "data_source_removed", None)
        connect_fn = getattr(removed_sig, "connect", None)
        if callable(connect_fn):
            try:
                connect_fn(self._handle_source_removed)
            except Exception as e:
                logger.debug(f"[IngestionWorker] Could not connect data_source_removed signal: {e}")

        # Subscribe to hub's accepted packet stream
        self.hub.register_listener(self._handle_hub_packet)

        # Sync existing data sources from state into adapters
        self._sync_registered_sources()

    def _handle_source_removed(self, source_id: str) -> None:
        """Invoked when a source is removed from AppState; propagates to hub and Go daemon."""
        self._known_source_ids.discard(source_id)
        self.hub.unregister_source(source_id)

    def unregister_source(self, source_id: str) -> None:
        """Explicitly unregisters a data source from all adapters."""
        self._handle_source_removed(source_id)

    def _sync_registered_sources(self) -> None:
        """
        Synchronizes all active adapters with currently registered data sources.
        Performs bidirectional reconciliation (removes deleted sources and adds new ones).
        """
        sources = self.app_state.get_all_data_sources()
        current_ids = {src.id for src in sources}

        # 1. Unregister sources that were removed from AppState
        removed_ids = self._known_source_ids - current_ids
        for rem_id in removed_ids:
            self.hub.unregister_source(rem_id)

        # 2. Register/update active sources
        for src in sources:
            self.hub.register_source(src)

        self._known_source_ids = current_ids

    def start(self) -> None:
        """Starts ingestion adapters."""
        logger.info("[IngestionWorker] Starting Ingestion Hub and Go Gateway Adapter...")
        self._sync_registered_sources()
        self.hub.start_all()
        logger.info("[IngestionWorker] 🚀 Ingestion Engine Online (Unified Go Gateway).")

    def stop(self) -> None:
        """Gracefully stops all ingestion adapters."""
        logger.info("[IngestionWorker] Stopping Ingestion Hub and Go Gateway...")
        self.hub.stop_all()

    def check_global_fetch(self, current_time: float) -> None:
        """
        Called by the main cycle to evaluate polling checks across adapters.
        """
        # Ensure new/updated sources are synced to Go poller
        self._sync_registered_sources()
        self.hub.check_poll(current_time)

    def get_pipeline(self) -> IngestionPipeline:
        """Exposes the pipeline for Linguist/Quarantine checks."""
        return self.pipeline

    def _handle_hub_packet(self, source_id: str, payload: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Invoked when an accepted packet is authenticated by the Zero Trust pipeline.
        Emits thread-safe Qt data_ready signal downstream to InferenceEngine and UI.
        """
        self.data_ready.emit(source_id, payload)

