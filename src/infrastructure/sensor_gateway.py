# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import logging
import threading
from typing import Any, Callable, Dict, List, Optional

from PyQt6.QtCore import QObject, pyqtSignal

from src.infrastructure.parsers import (
    BasePayloadParser,
    CsvPayloadParser,
    IPayloadParser,
    JsonPayloadParser,
    PolyglotPayloadParser,
    RawFallbackPayloadParser,
    XmlPayloadParser,
    create_default_parser_registry,
)
from src.infrastructure.sensor_id_extractor import SensorIdExtractor
from src.interfaces.sensor_gateway import IPolyglotPayloadParser, ISensorGateway, ISensorIdExtractor
from src.utils.logging_setup import get_logger

logger = get_logger("SensorGateway")


# Global parser registry instance for backward compatibility
global_parser_registry = create_default_parser_registry()


# =============================================================================
# IN-MEMORY COMPATIBILITY STUBS (Network binding fully delegated to Go Gateway)
# =============================================================================

class SensorHTTPServer:
    """In-memory stub preserving type references without opening OS network sockets."""
    def __init__(self, *args, **kwargs):
        pass


class IngestionHandler:
    """In-memory stub preserving type references without HTTP socket handling."""
    pass


# =============================================================================
# SENSOR GATEWAY FACADE & ORCHESTRATOR (SOLID Architecture)
# =============================================================================

class SensorGateway(QObject):
    """
    The Inbound Sensor Gateway (Facade & Orchestrator).
    
    SOLID Architecture:
    - [SRP] Exclusively coordinates ingestion lifecycle, parser dispatching, ID resolution, and data emission.
    - [OCP] Open for custom parsers and ID extractors via dependency injection.
    - [LSP] Conforms structurally to ISensorGateway protocol.
    - [ISP] Replaces heavy QThread inheritance with composed background thread execution.
    - [DIP] Decoupled from static globals; supports both pure Python callbacks and Qt signals.
    """

    # Qt Inbound Signals (Sensor -> Synapse Runtime)
    data_received = pyqtSignal(str, object)
    server_started = pyqtSignal(int)
    server_error = pyqtSignal(str)

    def __init__(
        self,
        host: str = '0.0.0.0',
        port: int = 8080,
        parser_registry: Optional[IPolyglotPayloadParser] = None,
        id_extractor: Optional[ISensorIdExtractor] = None,
        parent: Optional[QObject] = None,
    ):
        super().__init__(parent)
        self.host = host
        self.port = port
        self._parser_registry: IPolyglotPayloadParser = parser_registry or create_default_parser_registry()
        self._id_extractor: ISensorIdExtractor = id_extractor or SensorIdExtractor()

        self._httpd: Optional[SensorHTTPServer] = None
        self._server_thread: Optional[threading.Thread] = None
        self._is_running = False
        self._listeners: List[Callable[[str, Dict[str, Any]], None]] = []

    # =========================================================================
    # FACADE ORCHESTRATION PIPELINE
    # =========================================================================

    def register_listener(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Allows pure Python subscribers to receive sensor packets without Qt signal dependencies."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unregister_listener(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """Removes a registered callback."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def handle_inbound_request(
        self,
        content_type: str,
        decoded_body: str,
        client_ip: str,
        request_path: str,
        content_length: int,
    ) -> Dict[str, Any]:
        """
        Orchestration pipeline:
        1. Parse raw payload via polyglot strategy
        2. Identify device ID via extractor heuristic
        3. Notify Python listeners and emit Qt signals
        """
        # 1. Universal Parsing (Delegated Strategy)
        payload = self._parser_registry.parse(content_type, decoded_body)

        # 2. Identify Source (Delegated Extractor with URL path support)
        source_id = self._id_extractor.extract(payload, client_ip, request_path=request_path)

        # 3. Formatted Terminal Reception Log
        fmt_desc = content_type if content_type else "raw/auto"
        logger.info(
            f"📥 [SensorGateway] Recebido POST em '{request_path}' -> ID='{source_id}' (IP: {client_ip}) | "
            f"Formato: {fmt_desc} | Tamanho: {content_length} bytes"
        )

        # 4. Notify Listeners (Pure Callback Interface)
        for listener in self._listeners:
            try:
                listener(str(source_id), payload)
            except Exception as ex:
                logger.error(f"[SensorGateway] Error in packet listener: {ex}", exc_info=True)

        # 5. Emit RAW Payload to Engine (Thread-Safe Qt Signal)
        self.data_received.emit(str(source_id), payload)

        return payload

    # =========================================================================
    # LIFECYCLE MANAGEMENT
    # =========================================================================

    def start(self) -> None:
        """Enables in-memory gateway packet processing (network binding fully handled by Go)."""
        if self._is_running:
            logger.debug("[SensorGateway] In-memory dispatcher already active.")
            return

        self._is_running = True
        self.server_started.emit(self.port)
        logger.info(f"📥 [SensorGateway] In-Memory Packet Dispatcher Active (Network Ingress fully isolated in Go).")

    def _run_server(self) -> None:
        """No-op stub preserving backward-compatible signature."""
        pass

    def stop(self) -> None:
        """Stops the in-memory gateway packet dispatcher."""
        self._is_running = False
        logger.info("[SensorGateway] In-memory dispatcher stopped.")

    def is_running(self) -> bool:
        """Returns True if the gateway server is actively listening."""
        return self._is_running

    def isRunning(self) -> bool:
        """Backward-compatible alias matching QThread API."""
        return self.is_running()

    def wait(self, timeout: Optional[float] = None) -> None:
        """Backward-compatible alias matching QThread.wait()."""
        if self._server_thread and self._server_thread.is_alive():
            self._server_thread.join(timeout=timeout)


__all__ = [
    "IPayloadParser",
    "BasePayloadParser",
    "JsonPayloadParser",
    "XmlPayloadParser",
    "CsvPayloadParser",
    "RawFallbackPayloadParser",
    "PolyglotPayloadParser",
    "create_default_parser_registry",
    "global_parser_registry",
    "SensorIdExtractor",
    "SensorHTTPServer",
    "IngestionHandler",
    "SensorGateway",
]
