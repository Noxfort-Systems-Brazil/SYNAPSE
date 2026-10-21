# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Pure Facade / Orchestrator for Go Subprocess Transport (SOLID: SRP, LSP, ISP, DIP).
Coordinates the Go binary manager, OS process runner, and NDJSON event dispatcher
behind a clean, unified contract.
"""

import json
import threading
from typing import Any, Dict, Optional

from src.go.binary_manager import GoBinaryManager
from src.go.pipe_dispatcher import GoPipeDispatcher
from src.go.pipe_process import GoPipeProcess
from src.interfaces.gateway_transport import IGatewayTransport, PacketCallback
from src.utils.logging_setup import get_logger

logger = get_logger("GoSubprocessTransport")


class GoSubprocessTransport(IGatewayTransport):
    """
    Pure Facade orchestrating the Go Ingestion Gateway daemon over anonymous OS pipes.
    """

    def __init__(
        self,
        bin_path: Optional[str] = None,
        binary_manager: Optional[GoBinaryManager] = None,
        process: Optional[GoPipeProcess] = None,
        dispatcher: Optional[GoPipeDispatcher] = None,
    ):
        self.binary_manager = binary_manager or GoBinaryManager(bin_path=bin_path)
        self.process = process or GoPipeProcess(bin_path=self.binary_manager.bin_path)
        self.dispatcher = dispatcher or GoPipeDispatcher()
        self._bin_path = self.binary_manager.bin_path

    @property
    def _process(self):
        return self.process._process

    @_process.setter
    def _process(self, proc):
        self.process._process = proc

    @property
    def _on_packet(self):
        return self.dispatcher._on_packet

    @_on_packet.setter
    def _on_packet(self, cb):
        self.dispatcher.set_packet_callback(cb)

    def _stdout_reader_loop(self) -> None:
        """Backward-compatible loop delegation for tests."""
        if self.process.stdout:
            self.dispatcher._stdout_loop(self.process.stdout)

    @classmethod
    def ensure_compiled(cls, bin_path: Optional[str] = None) -> bool:
        """Backward-compatible utility delegating to GoBinaryManager."""
        mgr = GoBinaryManager(bin_path=bin_path)
        return mgr.ensure_ready()

    @property
    def is_running(self) -> bool:
        """Returns True if the subprocess is alive and executing."""
        return self.process.is_running

    def start(self, on_packet_received: PacketCallback) -> bool:
        """
        Orchestrates startup sequence:
        1. Ensures executable binary exists.
        2. Spawns low-level process with anonymous pipes.
        3. Attaches event dispatcher to pipes.
        """
        if self.is_running:
            logger.warning("[GoTransport] Subprocess already running.")
            return True

        if not self.binary_manager.ensure_ready():
            logger.error(f"[GoTransport] Cannot start: binary {self.binary_manager.bin_path} is unavailable.")
            return False

        self.dispatcher.set_packet_callback(on_packet_received)

        if not self.process.spawn():
            return False

        if self.process.stdout and self.process.stderr:
            self.dispatcher.start(self.process.stdout, self.process.stderr)

        return True

    def send_command(self, cmd_dict: Dict[str, Any]) -> bool:
        """Serializes and sends a control command to Go STDIN pipe."""
        if not self.is_running:
            return False
        line = json.dumps(cmd_dict)
        return self.process.write_line(line)

    def ping(self) -> bool:
        return self.send_command({"cmd": "PING"})

    def request_stats(self) -> bool:
        return self.send_command({"cmd": "GET_STATS"})

    def register_poll_source(self, source_id: str, url: str, interval_sec: float = 10.0) -> bool:
        """Instructs Go poller engine to poll an external REST endpoint."""
        return self.send_command({
            "cmd": "REGISTER_POLL_SOURCE",
            "source_id": source_id,
            "url": url,
            "interval_sec": interval_sec,
        })

    def unregister_poll_source(self, source_id: str) -> bool:
        """Instructs Go poller engine to stop polling a REST endpoint."""
        return self.send_command({
            "cmd": "UNREGISTER_POLL_SOURCE",
            "source_id": source_id,
        })

    def test_duckdns(self, domain: str, token: str, timeout: float = 8.0) -> Dict[str, Any]:
        """
        Delegates DuckDNS connection testing exclusively to the Go Gateway.
        Sends TEST_DUCKDNS over STDIN and awaits DUCKDNS_TEST_RESULT from STDOUT pipe.
        Zero Python sockets, zero Python HTTP requests.
        """
        if not self.is_running:
            return {
                "status": "error",
                "error": "Go Gateway não está em execução. Inicie o gateway antes de testar a conexão.",
            }

        result_event = threading.Event()
        result_box: Dict[str, Any] = {}

        def _on_test_result(msg: Dict[str, Any]) -> None:
            result_box.update(msg)
            result_event.set()

        prev_handler = self.dispatcher._handlers.get("DUCKDNS_TEST_RESULT")
        self.dispatcher.register_handler("DUCKDNS_TEST_RESULT", _on_test_result)
        try:
            sent = self.send_command({
                "cmd": "TEST_DUCKDNS",
                "domain": domain,
                "token": token,
            })
            if not sent:
                return {
                    "status": "error",
                    "error": "Falha ao enviar comando de teste para o Go Gateway.",
                }

            if not result_event.wait(timeout=timeout):
                return {
                    "status": "error",
                    "error": f"Tempo esgotado ({timeout}s) aguardando resposta da API DuckDNS via Go Gateway.",
                }

            status = result_box.get("status", "ERROR")
            is_ok = status.upper() == "OK"
            latency = result_box.get("latency_ms", 0)
            msg = result_box.get("message", "")
            return {
                "status": "ok" if is_ok else "error",
                "message": msg if is_ok else None,
                "error": msg if not is_ok else None,
                "domain": f"{domain}.duckdns.org",
                "latency_ms": latency,
            }
        finally:
            if prev_handler:
                self.dispatcher.register_handler("DUCKDNS_TEST_RESULT", prev_handler)

    @property
    def is_caddy_running(self) -> bool:
        """Returns True if Caddy is running according to latest Go status event."""
        return bool(self.dispatcher.last_caddy_status.get("caddy_running", False))

    @property
    def caddy_port(self) -> int:
        """Returns the active HTTPS port reported by Caddy in Go."""
        return int(self.dispatcher.last_caddy_status.get("caddy_port", 443))

    @property
    def last_caddy_status(self) -> Dict[str, Any]:
        return self.dispatcher.last_caddy_status

    @property
    def last_duckdns_status(self) -> Dict[str, Any]:
        return self.dispatcher.last_duckdns_status

    def stop(self, timeout: float = 2.0) -> None:
        """
        Gracefully terminates Go gateway:
        1. Sends SHUTDOWN command.
        2. Closes STDIN pipe.
        3. Waits for process termination.
        4. Stops reader threads.
        """
        if self.process.is_running:
            self.send_command({"cmd": "SHUTDOWN"})
            self.process.close_stdin()
            self.process.terminate_gracefully(timeout=timeout)

        self.dispatcher.stop()
        logger.info("[GoTransport] Go Ingestion Gateway stopped.")
