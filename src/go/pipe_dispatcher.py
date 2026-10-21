# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Anonymous Pipe Event Dispatcher (SOLID: SRP, OCP).
Supervises background I/O reader threads and routes incoming NDJSON events
via an open, extensible handler registry.
"""

import json
import threading
from typing import IO, Any, Callable, Dict, Optional

from src.interfaces.gateway_transport import PacketCallback
from src.utils.logging_setup import get_logger

logger = get_logger("GoPipeDispatcher")

EventHandler = Callable[[Dict[str, Any]], None]


class GoPipeDispatcher:
    """
    Decodes newline-delimited JSON (NDJSON) messages from the Go gateway STDOUT pipe
    and dispatches them to registered event handlers without modifying core reader logic.
    """

    def __init__(self, on_packet_received: Optional[PacketCallback] = None):
        self._on_packet = on_packet_received
        self._handlers: Dict[str, EventHandler] = {}
        self._stdout_thread: Optional[threading.Thread] = None
        self._stderr_thread: Optional[threading.Thread] = None
        self._is_running = False

        self.last_duckdns_status: Dict[str, Any] = {}
        self.last_caddy_status: Dict[str, Any] = {}

        # Register standard built-in handlers
        self._register_default_handlers()

    def set_packet_callback(self, callback: PacketCallback) -> None:
        """Sets or updates the high-frequency packet emission callback."""
        self._on_packet = callback

    def register_handler(self, event_name: str, handler: EventHandler) -> None:
        """
        Extensible event registration (OCP).
        Enables new Go events to be handled dynamically without modifying this class.
        """
        self._handlers[event_name] = handler

    def _register_default_handlers(self) -> None:
        self.register_handler("PACKET", self._handle_packet)
        self.register_handler("GATEWAY_ONLINE", self._handle_gateway_online)
        self.register_handler("MQTT_CONNECTED", self._handle_mqtt_connected)
        self.register_handler("PONG", self._handle_pong)
        self.register_handler("STATS", self._handle_stats)
        self.register_handler("GATEWAY_ERROR", self._handle_gateway_error)
        self.register_handler("DUCKDNS_STATUS", self._handle_duckdns_status)
        self.register_handler("DUCKDNS_TEST_RESULT", self._handle_duckdns_test_result)
        self.register_handler("CADDY_STATUS", self._handle_caddy_status)

    def _handle_duckdns_status(self, msg: Dict[str, Any]) -> None:
        self.last_duckdns_status = msg
        logger.info(f"🦆 [GoGateway] DuckDNS Status: {msg.get('status')} - {msg.get('message')}")

    def _handle_duckdns_test_result(self, msg: Dict[str, Any]) -> None:
        logger.info(f"🦆 [GoGateway] DuckDNS Test Result: {msg.get('status')} - {msg.get('message')}")

    def _handle_caddy_status(self, msg: Dict[str, Any]) -> None:
        self.last_caddy_status = msg
        logger.info(f"🛡️ [GoGateway] Caddy Status: {msg.get('status')} (Port: {msg.get('caddy_port')}) - {msg.get('message')}")

    def _handle_packet(self, msg: Dict[str, Any]) -> None:
        if not self._on_packet:
            return

        source_id = msg.get("source_id", "unknown")
        payload = msg.get("payload")
        metadata = {
            "client_ip": msg.get("client_ip"),
            "timestamp": msg.get("timestamp"),
            "transport": msg.get("transport", "HTTP-Push-Go"),
            "content_type": msg.get("content_type"),
        }
        try:
            self._on_packet(source_id, payload, metadata)
        except Exception as err:
            logger.error(f"[GoPipeDispatcher] Error executing packet callback: {err}", exc_info=True)

    def _handle_gateway_online(self, msg: Dict[str, Any]) -> None:
        logger.info(f"📥 [GoGateway] Ingestion Gateway Online at {msg.get('error', '')}")

    def _handle_mqtt_connected(self, msg: Dict[str, Any]) -> None:
        broker = msg.get("broker", "tcp://localhost:1883")
        topics = msg.get("topics", [])
        logger.info(f"📡 [GoGateway] MQTT broker connected at {broker}. Subscribed topics: {topics}")

    def _handle_pong(self, msg: Dict[str, Any]) -> None:
        logger.debug("[GoGateway] Received PONG from Go gateway.")

    def _handle_stats(self, msg: Dict[str, Any]) -> None:
        logger.debug(f"[GoGateway] Metrics: {msg.get('stats')}")

    def _handle_gateway_error(self, msg: Dict[str, Any]) -> None:
        logger.error(f"❌ [GoGateway] Gateway Error: {msg.get('error')}")

    def start(self, stdout_pipe: IO[str], stderr_pipe: IO[str]) -> None:
        """Starts background reader threads for STDOUT and STDERR pipes."""
        self._is_running = True

        self._stdout_thread = threading.Thread(
            target=self._stdout_loop,
            args=(stdout_pipe,),
            name="GoDispatcher-STDOUT-Reader",
            daemon=True,
        )
        self._stdout_thread.start()

        self._stderr_thread = threading.Thread(
            target=self._stderr_loop,
            args=(stderr_pipe,),
            name="GoDispatcher-STDERR-Reader",
            daemon=True,
        )
        self._stderr_thread.start()

    def _stdout_loop(self, stdout_pipe: IO[str]) -> None:
        """Reads newline-delimited JSON packets from STDOUT."""
        logger.debug("[GoPipeDispatcher] STDOUT reader thread active.")
        try:
            for line in stdout_pipe:
                line = line.strip()
                if not line:
                    continue

                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    logger.debug(f"[GoPipeDispatcher] Non-JSON line on STDOUT: {line}")
                    continue

                event = msg.get("event")
                handler = self._handlers.get(event)
                if handler:
                    try:
                        handler(msg)
                    except Exception as h_err:
                        logger.error(f"[GoPipeDispatcher] Error in event handler '{event}': {h_err}")
                else:
                    logger.debug(f"[GoPipeDispatcher] Unhandled event: {event}")

        except Exception as ex:
            if self._is_running:
                logger.debug(f"[GoPipeDispatcher] STDOUT reader terminated: {ex}")
        finally:
            self._is_running = False

    def _stderr_loop(self, stderr_pipe: IO[str]) -> None:
        """Reads diagnostics and logs from STDERR and forwards to Python logger."""
        try:
            for line in stderr_pipe:
                line = line.strip()
                if not line:
                    continue
                logger.info(f"[GoCore] {line}")
        except Exception:
            pass

    def stop(self, join_timeout: float = 0.5) -> None:
        """Stops loops and joins reader threads."""
        self._is_running = False
        if self._stdout_thread and self._stdout_thread.is_alive():
            self._stdout_thread.join(timeout=join_timeout)
        if self._stderr_thread and self._stderr_thread.is_alive():
            self._stderr_thread.join(timeout=join_timeout)
