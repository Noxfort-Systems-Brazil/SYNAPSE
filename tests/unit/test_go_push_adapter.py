# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import json
from unittest.mock import MagicMock, patch

import pytest

from src.adapters.go_push_adapter import GoPushAdapter, GoIngestionAdapter
from src.domain.app_state import AppState
from src.domain.entities import DataSource, SourceStatus
from src.go.subprocess_transport import GoSubprocessTransport
from src.interfaces.ingestion_adapters import IIngestionAdapter
from src.workers.ingestion_worker import IngestionWorker


def test_go_push_adapter_conforms_to_interface():
    adapter = GoPushAdapter()
    assert isinstance(adapter, IIngestionAdapter)
    assert adapter.adapter_id == "go_ingestion_gateway"
    assert adapter.transport_name == "Go-Gateway"
    assert adapter.is_running is False


def test_go_push_adapter_packet_emission():
    adapter = GoPushAdapter()
    received_packets = []

    def on_packet(source_id, payload, meta=None):
        received_packets.append((source_id, payload, meta))

    adapter.start(on_packet)
    assert adapter.is_running is True

    # Simulate arrival of an ingested packet from Go over anonymous pipe
    adapter._on_transport_packet(
        source_id="radar_north",
        payload={"speed": 68.5, "vehicles": 4},
        metadata={"client_ip": "192.168.1.10", "timestamp": 1726000000.0},
    )

    assert len(received_packets) == 1
    sid, payload, meta = received_packets[0]
    assert sid == "radar_north"
    assert payload["speed"] == 68.5
    assert meta["transport"] == "Go-Gateway"
    assert meta["client_ip"] == "192.168.1.10"

    adapter.stop()
    assert adapter.is_running is False


def test_go_subprocess_transport_stdout_parsing():
    transport = GoSubprocessTransport()
    received = []

    def on_packet(sid, payload, meta):
        received.append((sid, payload, meta))

    transport._on_packet = on_packet
    transport._is_running = True

    # Mock process stdout with simulated NDJSON stream
    simulated_stdout = [
        '{"event":"PACKET","source_id":"src_01","payload":{"temp":24.5},"client_ip":"10.0.0.1","transport":"HTTP-Push-Go"}\n',
        '{"event":"GATEWAY_ONLINE","status":"LISTENING"}\n',
        '{"event":"PONG","status":"OK"}\n',
    ]

    mock_proc = MagicMock()
    mock_proc.stdout = simulated_stdout
    transport._process = mock_proc

    transport._stdout_reader_loop()

    assert len(received) == 1
    sid, payload, meta = received[0]
    assert sid == "src_01"
    assert payload["temp"] == 24.5
    assert meta["client_ip"] == "10.0.0.1"


def test_ingestion_worker_with_go_gateway():
    app_state = AppState()
    worker = IngestionWorker(app_state)

    assert worker.pipeline is not None
    assert worker.hub is not None

    if worker.go_adapter:
        assert worker.hub.get_adapter("go_ingestion_gateway") is not None

    # Test packet routing through IngestionWorker to Qt data_ready signal
    signals = []
    worker.data_ready.connect(lambda sid, d: signals.append((sid, d)))

    src = DataSource(id="cam_mock", name="Mock Cam", is_local=True)
    app_state.add_data_source(src)

    worker._handle_hub_packet("cam_mock", {"flow": 120})

    assert len(signals) == 1
    assert signals[0][0] == "cam_mock"
    assert signals[0][1]["flow"] == 120


def test_go_push_adapter_delegates_polling_source():
    adapter = GoPushAdapter()
    with patch.object(adapter.transport, "register_poll_source") as mock_reg, \
         patch.object(adapter.transport, "unregister_poll_source") as mock_unreg:

        # 1. Local source: should not register as polling target
        local_src = DataSource(id="local_radar", name="Local Radar", is_local=True)
        adapter.register_source(local_src)
        mock_reg.assert_not_called()

        # 2. Global source: should delegate to Go poller
        global_src = DataSource(
            id="waze_global",
            name="Waze API",
            is_local=False,
            connection_string="https://api.waze.com/alerts",
            status=SourceStatus.QUARANTINE,
        )
        adapter.register_source(global_src)
        mock_reg.assert_called_once_with("waze_global", "https://api.waze.com/alerts", interval_sec=10.0)

        # 3. Unregister
        adapter.unregister_source("waze_global")
        mock_unreg.assert_called_once_with("waze_global")



def test_go_transport_spawns_cleanly_without_network_or_vpn_flags():
    """
    Asserts that Python transport spawns the compiled binary directly without
    managing ports, network sockets, or VPN parameters via CLI flags.
    """
    transport = GoSubprocessTransport(bin_path="/tmp/mock-gateway")
    with patch("subprocess.Popen") as mock_popen, \
         patch("threading.Thread") as mock_thread, \
         patch.object(transport, "ensure_compiled", return_value=True), \
         patch("os.path.isfile", return_value=True), \
         patch("os.access", return_value=True):

        transport.start(lambda s, d, m: None)
        cmd_args = mock_popen.call_args[0][0]

        # The command must be solely the binary path, with no network flags
        assert cmd_args == ["/tmp/mock-gateway"]
        assert "-port" not in cmd_args
        assert "-enable-vpn" not in cmd_args
        assert "-vpn-port" not in cmd_args
        assert "-enable-mqtt" not in cmd_args


def test_ingestion_worker_unregisters_source_on_app_state_signal():
    """
    Asserts that when a source is removed from AppState, IngestionWorker reacts to
    data_source_removed signal and propagates unregistration to Go gateway.
    """
    app_state = AppState()
    worker = IngestionWorker(app_state)

    # Mock the transport unregister method
    if worker.go_adapter:
        with patch.object(worker.go_adapter.transport, "unregister_poll_source") as mock_unreg:
            # 1. Add global polling source
            global_src = DataSource(
                id="waze_sp_01",
                name="Waze SP",
                is_local=False,
                connection_string="https://api.waze.com/traffic",
            )
            app_state.add_data_source(global_src)
            worker._sync_registered_sources()
            assert "waze_sp_01" in worker.go_adapter._registered_poll_sources

            # 2. Remove source from AppState (triggers signal data_source_removed)
            app_state.remove_data_source("waze_sp_01")

            # 3. Assert unregister command was dispatched
            assert "waze_sp_01" not in worker.go_adapter._registered_poll_sources
            mock_unreg.assert_called_once_with("waze_sp_01")


def test_ingestion_worker_reconciles_removed_sources_in_sync_loop():
    """
    Asserts that _sync_registered_sources reconciles removed sources even if
    the signal was bypassed, guaranteeing no orphan poller goroutines in Go.
    """
    app_state = AppState()
    worker = IngestionWorker(app_state)

    if worker.go_adapter:
        with patch.object(worker.go_adapter.transport, "unregister_poll_source") as mock_unreg:
            src = DataSource(
                id="tomtom_01",
                name="TomTom Feed",
                is_local=False,
                connection_string="https://api.tomtom.com/flow",
            )
            app_state.add_data_source(src)
            worker._sync_registered_sources()
            assert "tomtom_01" in worker._known_source_ids

            # Manually remove from repository without emitting signal
            app_state.sources._data_sources.pop("tomtom_01", None)

            # Periodic sync tick
            worker.check_global_fetch(12345.0)

            assert "tomtom_01" not in worker._known_source_ids
            assert "tomtom_01" not in worker.go_adapter._registered_poll_sources
            mock_unreg.assert_called_once_with("tomtom_01")



