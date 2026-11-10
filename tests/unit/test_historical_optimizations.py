# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import sys
import time
import logging
import tempfile
import pickle
import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock

from src.services.historical_manager import HistoricalManager
from src.meh.fallback_engine import FallbackEngine
from src.adapters.go_push_adapter import GoPushAdapter
from src.domain.entities import DataSource
from src.go.pipe_dispatcher import GoPipeDispatcher
from src.logging.interceptors import StreamToLogger
from src.utils.attention_utils import get_sdp_context


def test_historical_manager_singleton(qapp):
    """Verifies HistoricalManager behaves as a true singleton across multiple instantiations."""
    inst1 = HistoricalManager(lazy_load=True)
    inst2 = HistoricalManager(lazy_load=True)
    assert inst1 is inst2
    assert inst1._initialized is True


def test_fallback_engine_disk_caching(tmp_path):
    """Verifies that FallbackEngine saves and loads profiles from disk cache."""
    gold_file = tmp_path / "golden_v1.parquet"
    gold_file.write_bytes(b"dummy")

    # Create mock loader
    mock_loader = MagicMock()
    mock_loader.gold_path = str(gold_file)
    mock_loader.is_loaded = True
    mock_loader.group_column = "sensor_id"
    mock_loader.sensor_ids = ["s1"]

    # Sample dataframe
    df = pd.DataFrame({
        "timestamp": pd.date_range("2026-01-01", periods=10, freq="10s"),
        "sensor_id": ["s1"] * 10,
        "speed": [50.0] * 10,
        "density": [12.0] * 10,
    })
    mock_loader.data = df

    engine = FallbackEngine(mock_loader)
    engine.build_profiles(force_recompute=True)

    cache_file = tmp_path / "profiles_cache_v1.pkl"
    assert cache_file.exists()

    # Second call should load from cache
    engine2 = FallbackEngine(mock_loader)
    engine2.build_profiles(force_recompute=False)
    assert engine2.is_ready is True
    assert "s1" in engine2.sensor_profiles


def test_go_push_adapter_dedup():
    """Verifies GoPushAdapter does not send duplicate IPC commands for already registered sources."""
    mock_transport = MagicMock()
    adapter = GoPushAdapter(transport=mock_transport)

    src = DataSource(
        id="waze_global",
        name="Waze",
        is_local=False,
        connection_string="http://localhost:8088/api/waze"
    )

    # First registration -> should call transport
    adapter.register_source(src)
    assert mock_transport.register_poll_source.call_count == 1

    # Second registration with same URL -> should be ignored (no duplicate IPC)
    adapter.register_source(src)
    assert mock_transport.register_poll_source.call_count == 1

    # Unregister -> should clear cache and call transport
    adapter.unregister_source("waze_global")
    assert mock_transport.unregister_poll_source.call_count == 1
    assert "waze_global" not in adapter._registered_poll_sources


def test_go_pipe_dispatcher_mqtt():
    """Verifies that MQTT_CONNECTED event is handled properly without error."""
    dispatcher = GoPipeDispatcher()
    assert "MQTT_CONNECTED" in dispatcher._handlers

    # Dispatch event
    msg = {
        "event": "MQTT_CONNECTED",
        "broker": "tcp://localhost:1883",
        "topics": ["synapse/telemetry"]
    }
    # Should execute handler cleanly
    dispatcher._handlers["MQTT_CONNECTED"](msg)


def test_stream_to_logger_warning_classification():
    """Verifies that Python warnings sent to stderr are categorized as WARNING, not ERROR."""
    mock_logger = MagicMock()
    stream = StreamToLogger(mock_logger, log_level=logging.ERROR, stream_name="stderr")

    warning_text = "/path/test.py:10: FutureWarning: `sdp_kernel()` is deprecated."
    stream.write(warning_text)

    assert mock_logger.makeRecord.called
    assert mock_logger.makeRecord.call_args.kwargs["level"] == logging.WARNING


def test_get_sdp_context():
    """Verifies get_sdp_context enters and exits cleanly."""
    with get_sdp_context(enable_flash=True, enable_mem_efficient=True, enable_math=True):
        x = 1 + 1
    assert x == 2
