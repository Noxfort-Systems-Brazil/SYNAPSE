# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
from unittest.mock import patch, MagicMock
from src.infrastructure.monitor_client import MonitorClient
from src.services.telemetry_service import TelemetryService


def test_check_is_http():
    # HTTP URLs
    assert MonitorClient._check_is_http("https://medicochirurgical-stenophagous-london.ngrok-free.dev/api/telemetry") is True
    assert MonitorClient._check_is_http("http://192.168.1.50:8080/api/telemetry") is True
    assert MonitorClient._check_is_http("medicochirurgical.ngrok.io/api/telemetry") is True
    assert MonitorClient._check_is_http("api.mycloud.dev/telemetry") is True

    # MQTT hosts
    assert MonitorClient._check_is_http("localhost") is False
    assert MonitorClient._check_is_http("127.0.0.1") is False
    assert MonitorClient._check_is_http("192.168.1.100:1883") is False
    assert MonitorClient._check_is_http("broker.hivemq.com:1883") is False


def test_normalize_http_url():
    assert MonitorClient._normalize_http_url("https://ngrok-free.dev/api") == "https://ngrok-free.dev/api"
    assert MonitorClient._normalize_http_url("http://localhost:3000/api") == "http://localhost:3000/api"
    assert MonitorClient._normalize_http_url("my-host.ngrok-free.dev/api") == "https://my-host.ngrok-free.dev/api"


@patch("src.infrastructure.monitor_client.httpx.Client")
def test_http_telemetry_dispatch(mock_client_cls):
    mock_resp = MagicMock()
    mock_resp.is_success = True
    mock_resp.status_code = 200

    mock_client = MagicMock()
    mock_client.post.return_value = mock_resp
    mock_client_cls.return_value.__enter__.return_value = mock_client

    client = MonitorClient(
        host="https://my-api.ngrok-free.dev/api/telemetry",
        enabled=False
    )
    assert client.is_http is True
    assert client.http_url == "https://my-api.ngrok-free.dev/api/telemetry"

    # Test incident report
    client.enabled = True
    client.report_incident(category="SOFTWARE", level="CRITICAL", message="Test incident")

    assert mock_client.post.called
    call_args = mock_client.post.call_args
    assert call_args[0][0] == "https://my-api.ngrok-free.dev/api/telemetry"
    json_body = call_args[1]["json"]
    assert json_body["category"] == "SOFTWARE"
    assert json_body["level"] == "CRITICAL"
    assert json_body["message"] == "Test incident"
    assert json_body["origin"] == "synapse"


@patch("src.infrastructure.monitor_client.httpx.Client")
def test_connection_detailed_http(mock_client_cls):
    # Case 1: Success (200 OK)
    mock_resp_200 = MagicMock()
    mock_resp_200.is_success = True
    mock_resp_200.status_code = 200
    mock_client = MagicMock()
    mock_client.post.return_value = mock_resp_200
    mock_client_cls.return_value.__enter__.return_value = mock_client

    ok, msg = MonitorClient.test_connection_detailed("https://ngrok-free.dev/api/telemetry")
    assert ok is True
    assert "Conexão HTTP OK" in msg

    # Case 2: Server error (404 Not Found)
    mock_resp_404 = MagicMock()
    mock_resp_404.is_success = False
    mock_resp_404.status_code = 404
    mock_resp_404.text = "Not Found"
    mock_client.post.return_value = mock_resp_404

    ok, msg = MonitorClient.test_connection_detailed("https://ngrok-free.dev/api/telemetry")
    assert ok is False
    assert "404" in msg


def test_telemetry_service_hot_reconfigure(qapp):
    telemetry = TelemetryService()
    assert telemetry.enabled is False

    # Reconfigure to HTTP
    telemetry.reconfigure_telemetry(
        enabled=True,
        host="https://ngrok-free.dev/api/telemetry",
        port=443
    )
    assert telemetry.enabled is True
    assert telemetry.monitor_client is not None
    assert telemetry.monitor_client.is_http is True
    assert telemetry.monitor_client.http_url == "https://ngrok-free.dev/api/telemetry"

    # Stop / disable
    telemetry.reconfigure_telemetry(
        enabled=False,
        host="localhost",
        port=1883
    )
    assert telemetry.enabled is False
