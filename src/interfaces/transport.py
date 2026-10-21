# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Any, AsyncGenerator, Dict, Optional, Protocol, runtime_checkable


@runtime_checkable
class IHFTTransport(Protocol):
    """Low-level transport contract for raw gRPC/RPC operations."""
    
    @property
    def is_running(self) -> bool:
        ...

    @property
    def is_connected(self) -> bool:
        ...

    async def start_channel(self) -> None:
        """Initializes raw transport channel."""
        ...

    async def close(self) -> None:
        """Closes the transport channel gracefully."""
        ...

    async def ping(self, timeout: float = 2.0) -> bool:
        """Sends a handshake / heartbeat ping."""
        ...

    async def load_scenario(self, proto_scenario: Any, timeout: float = 60.0) -> Any:
        """Sends scenario/topology protobuf message to the server."""
        ...

    async def system_control(self, request: Any, timeout: float = 5.0) -> Any:
        """Sends a control command message to the server."""
        ...

    async def stream_traffic(self, frame_generator: AsyncGenerator[Any, None]) -> Any:
        """Streams traffic frames via bidirectional or client-streaming RPC."""
        ...


@runtime_checkable
class IHFTStreamer(Protocol):
    """High-frequency packet stream buffering and throttling contract."""

    def start(self) -> None:
        ...

    def stop(self) -> None:
        ...

    async def enqueue_frame(self, proto_frame: Any) -> None:
        ...

    def frame_generator(self) -> AsyncGenerator[Any, None]:
        ...


@runtime_checkable
class IHFTRecoveryManager(Protocol):
    """Resilience and automatic reconnection/recovery manager contract."""

    def set_recovery_payload(self, map_data: Dict[str, Any]) -> None:
        ...

    def get_recovery_payload(self) -> Optional[Dict[str, Any]]:
        ...

    async def perform_recovery(
        self,
        transport: IHFTTransport,
        serializer: Any,
        start_streaming_cb: Any
    ) -> bool:
        ...


@runtime_checkable
class IHFTConnector(Protocol):
    """High-level Facade contract for HFT link orchestration."""

    async def start_channel(self) -> None:
        ...

    async def start_streaming(self) -> None:
        ...

    async def close(self) -> None:
        ...

    async def ping(self) -> bool:
        ...

    async def send_scenario(self, map_data: Dict[str, Any]) -> bool:
        ...

    async def set_system_state(self, command: str) -> bool:
        ...

    async def enqueue_traffic_frame(self, frame_data: Dict[str, Any]) -> None:
        ...
