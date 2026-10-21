# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import time
import pytest
from unittest.mock import MagicMock, patch

from src.domain.app_state import AppState
from src.domain.entities import DataSource, SourceStatus, SourceType
from src.adapters.base_adapter import BaseIngestionAdapter
from src.adapters.go_push_adapter import GoPushAdapter
from src.adapters.ingestion_hub import IngestionHub
from src.interfaces.ingestion_adapters import IIngestionAdapter, IIngestionHub
from src.pipeline.ingestion_pipeline import IngestionPipeline
from src.workers.ingestion_worker import IngestionWorker


def test_adapters_protocol_conformance():
    """Verifies that GoPushAdapter and IngestionHub conform to runtime protocols."""
    go_adapter = GoPushAdapter()
    assert isinstance(go_adapter, IIngestionAdapter)
    assert go_adapter.adapter_id == "go_ingestion_gateway"
    assert go_adapter.transport_name == "Go-Gateway"

    pipeline = MagicMock(spec=IngestionPipeline)
    hub = IngestionHub(pipeline)
    assert isinstance(hub, IIngestionHub)


def test_ingestion_hub_lifecycle_and_routing():
    """Tests hub adapter registration, start/stop lifecycle and packet routing."""
    app_state = AppState()
    pipeline = IngestionPipeline(app_state)
    hub = IngestionHub(pipeline)

    # Register DataSource in state so Zero Trust allows it
    src = DataSource(id="cam_01", name="Camera Paulista", status=SourceStatus.QUARANTINE, is_local=True)
    app_state.add_data_source(src)

    received_packets = []

    def on_received(source_id, payload, meta):
        received_packets.append((source_id, payload, meta))

    hub.register_listener(on_received)

    # Create dummy custom adapter inheriting from BaseIngestionAdapter
    class CustomMockAdapter(BaseIngestionAdapter):
        def _do_start(self):
            pass

        def _do_stop(self):
            pass

        def simulate_inbound(self, sid, data):
            self.emit_packet(sid, data, metadata={"custom_field": 42})

    custom_adapter = CustomMockAdapter(adapter_id="custom_mock", transport_name="CustomProtocol")
    hub.register_adapter(custom_adapter)
    hub.start_all()

    assert hub.is_running
    assert custom_adapter.is_running

    # Emit data from adapter -> should route through pipeline into listener
    custom_adapter.simulate_inbound("cam_01", {"speed": 55.4, "flow": 120})

    assert len(received_packets) == 1
    sid, payload, meta = received_packets[0]
    assert sid == "cam_01"
    assert payload["speed"] == 55.4
    assert meta["transport"] == "CustomProtocol"
    assert meta["custom_field"] == 42

    # Check quarantine buffer in pipeline
    q_data = pipeline.get_quarantine_data("cam_01")
    assert len(q_data) == 1

    hub.stop_all()
    assert not hub.is_running
    assert not custom_adapter.is_running


def test_go_push_adapter_with_hub_and_pipeline():
    """Tests GoPushAdapter packet arrival, pipeline quarantine and listener dispatch."""
    app_state = AppState()
    pipeline = IngestionPipeline(app_state)
    hub = IngestionHub(pipeline)

    src = DataSource(id="radar_sp_01", name="Radar Marginal Tiete", status=SourceStatus.QUARANTINE, is_local=True)
    app_state.add_data_source(src)

    received = []
    hub.register_listener(lambda sid, data, meta: received.append((sid, data, meta)))

    go_adapter = GoPushAdapter(adapter_id="go_test")
    hub.register_adapter(go_adapter)
    hub.start_all()

    # Simulate packet coming from Go gateway over anonymous pipe
    go_adapter._on_transport_packet(
        source_id="radar_sp_01",
        payload={"flow": 850, "speed": 78.2},
        metadata={"client_ip": "10.0.0.5"},
    )

    assert len(received) == 1
    sid, payload, meta = received[0]
    assert sid == "radar_sp_01"
    assert payload["flow"] == 850
    assert meta["transport"] == "Go-Gateway"
    assert meta["client_ip"] == "10.0.0.5"

    # Verify pipeline quarantine received packet
    q_data = pipeline.get_quarantine_data("radar_sp_01")
    assert len(q_data) == 1
    assert q_data[0]["speed"] == 78.2

    hub.stop_all()


def test_ingestion_worker_integration_with_hub():
    """Verifies that IngestionWorker coordinates IngestionHub and delivers packets to data_ready signal."""
    app_state = AppState()
    worker = IngestionWorker(app_state)

    src_local = DataSource(id="local_radar", name="Local Radar", status=SourceStatus.QUARANTINE, is_local=True)
    app_state.add_data_source(src_local)

    received_signals = []
    worker.data_ready.connect(lambda sid, data: received_signals.append((sid, data)))

    # Direct packet routing into worker's hub listener
    worker._handle_hub_packet("local_radar", {"speed": 72.0, "vehicle_count": 8})

    assert len(received_signals) == 1
    sid, data = received_signals[0]
    assert sid == "local_radar"
    assert data["speed"] == 72.0

