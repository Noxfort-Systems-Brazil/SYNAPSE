# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Abstract Protocol for Gateway Subprocess Transport (SOLID: LSP, ISP, DIP).
Decouples high-level Ingestion Adapters from low-level OS process management.
"""

from typing import Any, Callable, Dict, Optional, Protocol, runtime_checkable

PacketCallback = Callable[[str, Any, Optional[Dict[str, Any]]], None]


@runtime_checkable
class IGatewayTransport(Protocol):
    """
    Contract for communication with the compiled high-throughput Go Gateway daemon.
    """

    @property
    def is_running(self) -> bool:
        """Returns True if the gateway daemon process is alive and healthy."""
        ...

    def start(self, on_packet_received: PacketCallback) -> bool:
        """Boots the gateway daemon and connects the incoming packet stream callback."""
        ...

    def stop(self, timeout: float = 2.0) -> None:
        """Gracefully terminates the gateway daemon."""
        ...

    def send_command(self, cmd_dict: Dict[str, Any]) -> bool:
        """Dispatches an arbitrary control command to the gateway over STDIN."""
        ...

    def ping(self) -> bool:
        """Sends a liveness PING command."""
        ...

    def request_stats(self) -> bool:
        """Requests current gateway operational metrics."""
        ...

    def register_poll_source(self, source_id: str, url: str, interval_sec: float = 10.0) -> bool:
        """Registers a remote API URL target for Go's concurrent poller engine."""
        ...

    def unregister_poll_source(self, source_id: str) -> bool:
        """Unregisters a remote API URL target from Go's poller engine."""
        ...
