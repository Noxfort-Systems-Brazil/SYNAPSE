# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import asyncio
import os
import sys
import time
from typing import Any, Dict, Optional, Type

# Ensure proto modules are reachable
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

import grpc
from proto import synapse_hft_pb2
from src.interfaces.transport import (
    IHFTConnector,
    IHFTRecoveryManager,
    IHFTStreamer,
    IHFTTransport,
)
from src.hft.hft_grpc_client import HFTGrpcClient
from src.hft.hft_recovery import HFTRecoveryManager
from src.hft.hft_serializers import HFTSerializer
from src.hft.hft_streamer import HFTStreamer
from src.utils.logging_setup import get_logger

logger = get_logger("HFT.Connector")


class GrpcConnector:
    """
    The High-Frequency Transport (HFT) Pure Facade & Orchestrator.
    """

    COMMAND_MAP = {
        "START": synapse_hft_pb2.ControlCommand.START,
        "STOP": synapse_hft_pb2.ControlCommand.STOP,
        "PAUSE": synapse_hft_pb2.ControlCommand.PAUSE,
    }

    def __init__(
        self,
        endpoint: str = "localhost:50051",
        transport: Optional[IHFTTransport] = None,
        streamer: Optional[IHFTStreamer] = None,
        recovery: Optional[IHFTRecoveryManager] = None,
        serializer: Optional[Type[HFTSerializer]] = None,
    ):
        self.endpoint = endpoint
        self.transport: IHFTTransport = transport or HFTGrpcClient(endpoint=endpoint)
        self.streamer: IHFTStreamer = streamer or HFTStreamer()
        self.recovery: IHFTRecoveryManager = recovery or HFTRecoveryManager()
        self.serializer = serializer or HFTSerializer

        self._stream_task: Optional[asyncio.Task] = None

    @property
    def is_running(self) -> bool:
        return self.transport.is_running

    @property
    def is_connected(self) -> bool:
        return self.transport.is_connected

    @property
    def channel(self) -> Any:
        return getattr(self.transport, "channel", None)

    @property
    def stub(self) -> Any:
        return getattr(self.transport, "stub", None)

    def set_recovery_payload(self, map_data: Dict[str, Any]) -> None:
        """Stores map definition into recovery manager for automatic re-upload."""
        self.recovery.set_recovery_payload(map_data)

    async def start_channel(self) -> None:
        """Initializes underlying transport channel."""
        await self.transport.start_channel()

    async def start_streaming(self) -> None:
        """Enables streamer buffer and starts background producer loop."""
        if not self.is_running:
            await self.start_channel()

        self.streamer.start()

        if not self._stream_task or self._stream_task.done():
            logger.info("🚀 Manual Stream Start Requested.")
            self._stream_task = asyncio.create_task(self._traffic_producer())

    async def close(self) -> None:
        """Gracefully closes streamer, producer task, and transport."""
        self.streamer.stop()

        if self._stream_task:
            self._stream_task.cancel()
            try:
                await self._stream_task
            except asyncio.CancelledError:
                pass
            self._stream_task = None

        await self.transport.close()
        logger.info("🔌 Tunnel Closed.")

    async def ping(self) -> bool:
        """Delegates Ping request to transport layer."""
        return await self.transport.ping()

    async def send_scenario(self, map_data: Dict[str, Any]) -> bool:
        """Serializes and sends scenario topology to the server."""
        self.set_recovery_payload(map_data)

        if not self.is_connected:
            logger.warning("⚠️ Cannot send scenario: Not connected.")
            return False

        logger.info("🗺️  Uploading Scenario File (Binary)...")
        try:
            proto_scenario = self.serializer.pack_scenario(map_data)
            response = await self.transport.load_scenario(proto_scenario, timeout=60.0)

            if getattr(response, "accepted", False):
                logger.info("✅ Scenario Upload Accepted.")
                return True
            else:
                msg = getattr(response, "message", "Unknown error")
                logger.error(f"❌ Scenario Rejected: {msg}")
                return False
        except Exception as e:
            logger.error(f"💥 Upload Failed: {e}", exc_info=True)
            return False

    async def set_system_state(self, command: str) -> bool:
        """Encodes command and sends control directive to server."""
        if not self.is_connected:
            return False

        cmd_enum = self.COMMAND_MAP.get(command, synapse_hft_pb2.ControlCommand.UNKNOWN)
        logger.info(f"🎮 Sending Command: {command}")

        try:
            req = synapse_hft_pb2.ControlCommand(action=cmd_enum)
            resp = await self.transport.system_control(req, timeout=5.0)

            if getattr(resp, "success", False):
                new_state = getattr(resp, "new_state", command)
                logger.info(f"-> System State is now: {new_state}")
                if command == "START":
                    await self.start_streaming()
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Command Failed: {e}", exc_info=True)
            return False

    async def enqueue_traffic_frame(self, frame_data: Dict[str, Any]) -> None:
        """Serializes incoming raw traffic dictionary and enqueues into streamer."""
        if not self.is_running:
            return
        try:
            proto_frame = self.serializer.pack_traffic_frame(frame_data)
            await self.streamer.enqueue_frame(proto_frame)
        except Exception:
            pass

    async def _traffic_producer(self) -> None:
        """
        Connects streamer generator to transport stream RPC.
        Handles disconnections and initiates auto-recovery transparently.
        """
        logger.info("🌊 Traffic Stream Loop Initiated.")
        backoff = 1.0

        while self.is_running:
            try:
                if not getattr(self.transport, "stub", None):
                    await self.start_channel()
                backoff = 1.0

                response = await self.transport.stream_traffic(self.streamer.frame_generator())
                logger.info(f"🏁 Stream Finished by Server: {getattr(response, 'state', 'DONE')}")

                if self.is_running:
                    logger.warning("⚠️ Stream ended unexpectedly. Starting Auto-Recovery...")
                    await self._handle_disconnection()

            except grpc.aio.AioRpcError as e:
                if not self.is_running:
                    break

                if e.code() in [grpc.StatusCode.UNAVAILABLE, grpc.StatusCode.CANCELLED]:
                    logger.warning(f"⚠️ Connection Lost ({e.code().name}). Starting Auto-Recovery...")
                    await self._handle_disconnection()
                else:
                    logger.error(f"💥 RPC Error: {e.code().name} - {e.details()}")
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 1.5, 5.0)

            except Exception as e:
                if self.is_running:
                    logger.error(f"💥 Generic Error: {e}", exc_info=True)
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 1.5, 5.0)

        logger.info("🌊 Traffic Stream Loop Ended.")

    async def _handle_disconnection(self) -> None:
        """Delegates auto-recovery routine to recovery manager."""
        recovered = await self.recovery.perform_recovery(
            transport=self.transport,
            serializer=self.serializer,
            set_system_state_cb=self.set_system_state,
        )
        if recovered:
            logger.info("♻️ Recovery Successful. Resuming Stream seamlessly.")
        else:
            logger.error("❌ Recovery Failed or Aborted.")
            await asyncio.sleep(2.0)
