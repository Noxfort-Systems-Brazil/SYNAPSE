# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import asyncio
import time
import logging
import sys
import os
from pathlib import Path
from typing import AsyncGenerator, Optional

# Ensure proto modules are reachable
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.append(project_root)

from proto import synapse_hft_pb2


class HFTStreamer:
    """
    Manages the high-frequency packet stream logic.
    """

    def __init__(self, queue_size: int = 200, min_interval_s: float = 0.150):
        self.transmit_queue: asyncio.Queue = asyncio.Queue(maxsize=queue_size)
        self.is_streaming = False
        self.min_interval = min_interval_s
        self.heartbeat_interval = 0.25
        self.freq_logger = self._setup_frequency_logger()

    def _setup_frequency_logger(self) -> logging.Logger:
        """Configures a dedicated logger to track transmission intervals."""
        log_dir = Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "hft_transmission_rate.log"

        logger = logging.getLogger("HFT_Frequency")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            fh = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            formatter = logging.Formatter('%(asctime)s - %(message)s')
            fh.setFormatter(formatter)
            logger.addHandler(fh)

        return logger

    def start(self):
        self.is_streaming = True

    def stop(self):
        self.is_streaming = False

    async def enqueue_frame(self, proto_frame: synapse_hft_pb2.TrafficFrame):
        """
        Adds a pre-serialized frame to the buffer.
        Drops oldest if full (Traffic data is time-sensitive; old data is useless).
        """
        if not self.is_streaming:
            return

        try:
            if self.transmit_queue.full():
                try:
                    self.transmit_queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            self.transmit_queue.put_nowait(proto_frame)
        except Exception:
            pass

    async def frame_generator(self) -> AsyncGenerator[synapse_hft_pb2.TrafficFrame, None]:
        """
        The Core Generator that yields frames to the gRPC Stub.
        Implements Throttling and fast Heartbeats.
        """
        self.freq_logger.info("Stream Started (Generator Init)")
        yield self._create_heartbeat()
        last_send_time = time.time()

        while self.is_streaming:
            try:
                loop_start = time.perf_counter()

                try:
                    frame = await asyncio.wait_for(
                        self.transmit_queue.get(),
                        timeout=self.heartbeat_interval
                    )
                    is_hb = False
                except asyncio.TimeoutError:
                    frame = self._create_heartbeat()
                    is_hb = True

                fetch_time = (time.perf_counter() - loop_start) * 1000

                now = time.time()
                elapsed = now - last_send_time
                throttle_time = 0.0

                if elapsed < self.min_interval:
                    sleep_time = self.min_interval - elapsed
                    await asyncio.sleep(sleep_time)
                    now = time.time()
                    elapsed = now - last_send_time
                    throttle_time = sleep_time * 1000

                if elapsed * 1000 > 280:
                    self.freq_logger.warning(f"⚠️ SYNAPSE DELAY DETECTED! Elapsed: {elapsed*1000:.1f}ms before yield. Fetch took: {fetch_time:.1f}ms")

                t_yield = time.perf_counter()
                yield frame
                yield_time = (time.perf_counter() - t_yield) * 1000

                if yield_time > 50:
                    self.freq_logger.warning(f"⚠️ NETWORK/CARINA DELAY DETECTED! gRPC yield took: {yield_time:.1f}ms")

                if not is_hb or yield_time > 50 or elapsed * 1000 > 280:
                    seq_str = "HB" if is_hb else str(frame.sequence_id)
                    self.freq_logger.info(
                        f"Sent Delta: {elapsed*1000:.1f}ms | Seq: {seq_str} | "
                        f"Fetch: {fetch_time:.1f}ms | Throttle: {throttle_time:.1f}ms | gRPC_Yield: {yield_time:.1f}ms"
                    )

                last_send_time = now

            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[HFT-Streamer] Gen Error: {e}")
                await asyncio.sleep(0.5)

    def _create_heartbeat(self) -> synapse_hft_pb2.TrafficFrame:
        """Creates an empty frame to keep connection alive."""
        frame = synapse_hft_pb2.TrafficFrame()
        frame.timestamp = time.time()
        frame.sequence_id = 0
        return frame
