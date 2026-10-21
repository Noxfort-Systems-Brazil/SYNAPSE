# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import time
import httpx
import pytest

from src.go.subprocess_transport import GoSubprocessTransport


class MockAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"accidents": 2, "congestion_index": 0.85}')

    def log_message(self, format, *args):
        pass  # Suppress console noise


def test_go_gateway_e2e_anonymous_pipes(monkeypatch):
    """
    End-to-End Test for Push Ingestion:
    1. Spawns compiled Go gateway on test port (18099) via env var.
    2. Sends real HTTP POST to Go gateway.
    3. Verifies packet is transmitted to Python via STDOUT pipe in memory.
    4. Terminates Go gateway via STDIN pipe.
    """
    test_port = 18099
    monkeypatch.setenv("SYNAPSE_GATEWAY_PORT", str(test_port))
    monkeypatch.setenv("SYNAPSE_GATEWAY_HOST", "127.0.0.1")
    transport = GoSubprocessTransport()

    received_packets = []

    def on_packet(source_id, payload, meta):
        received_packets.append((source_id, payload, meta))

    assert transport.start(on_packet_received=on_packet) is True
    time.sleep(0.3)  # Allow HTTP server to bind

    try:
        # Send HTTP POST from camera simulation
        with httpx.Client(timeout=2.0) as client:
            resp = client.post(
                f"http://127.0.0.1:{test_port}/camera_lane_1",
                json={"speed": 88.4, "occupancy": 0.35, "vehicle_type": "truck"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "ACCEPTED"
            assert data["source_id"] == "camera_lane_1"

        # Wait for pipe buffer to arrive in Python thread
        time.sleep(0.2)

        assert len(received_packets) == 1
        sid, payload, meta = received_packets[0]
        assert sid == "camera_lane_1"
        assert payload["speed"] == 88.4
        assert payload["vehicle_type"] == "truck"
        assert meta["transport"] == "HTTP-Push-Go"
        assert meta["client_ip"] == "127.0.0.1"

    finally:
        transport.stop(timeout=1.0)
        assert transport.is_running is False


def test_go_gateway_e2e_poller_anonymous_pipes(monkeypatch):
    """
    End-to-End Test for HTTP Poller:
    1. Spawns mock HTTP API server (simulating Waze/external API).
    2. Spawns compiled Go gateway.
    3. Python sends REGISTER_POLL_SOURCE command via STDIN pipe.
    4. Go poller actively fetches the mock API and sends packet to Python via STDOUT pipe.
    5. Verifies packet arrives in Python callback.
    """
    # 1. Start local mock external server
    mock_server = HTTPServer(("127.0.0.1", 18077), MockAPIHandler)
    server_thread = threading.Thread(target=mock_server.serve_forever, daemon=True)
    server_thread.start()

    test_port = 18098
    monkeypatch.setenv("SYNAPSE_GATEWAY_PORT", str(test_port))
    monkeypatch.setenv("SYNAPSE_GATEWAY_HOST", "127.0.0.1")
    transport = GoSubprocessTransport()
    polled_packets = []

    def on_packet(source_id, payload, meta):
        polled_packets.append((source_id, payload, meta))

    assert transport.start(on_packet_received=on_packet) is True
    time.sleep(0.3)

    try:
        # Instruct Go daemon to poll our mock server every 200ms
        assert transport.register_poll_source(
            source_id="waze_external_feed",
            url="http://127.0.0.1:18077/feed",
            interval_sec=0.2,
        ) is True

        # Wait for Go's initial fetch and pipe delivery
        time.sleep(0.4)

        assert len(polled_packets) >= 1
        sid, payload, meta = polled_packets[0]
        assert sid == "waze_external_feed"
        assert payload["accidents"] == 2
        assert payload["congestion_index"] == 0.85
        assert meta["client_ip"] == "http://127.0.0.1:18077/feed"

    finally:
        transport.stop(timeout=1.0)
        mock_server.shutdown()
        mock_server.server_close()
