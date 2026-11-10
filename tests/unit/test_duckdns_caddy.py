# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch

from src.database.db_settings_manager import DatabaseSettingsManager
from src.infrastructure.network_service import NetworkService
from src.handlers.duckdns_handler import DuckDnsHandler
from src.ipc.ipc_protocol import IpcMessage


@pytest.fixture
def temp_settings_file():
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".ini") as f:
        f.write("[DUCKDNS]\n")
        f.write("domain = saopaulo-transito\n")
        f.write("token = mock-token-1234\n")
        f.write("enabled = true\n")
        f.write("caddy_enabled = true\n")
        f.write("port = 8081\n")
        f.write("https_port = 443\n")
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.remove(temp_path)


def test_duckdns_settings_load_and_save(temp_settings_file):
    mgr = DatabaseSettingsManager(settings_path=temp_settings_file)
    cfg = mgr.load_duckdns_settings()

    assert cfg["domain"] == "saopaulo-transito"
    assert cfg["token"] == "mock-token-1234"
    assert cfg["enabled"] is True
    assert cfg["caddy_enabled"] is True
    assert cfg["port"] == 8081
    assert cfg["https_port"] == 443

    # Save new settings
    cfg["domain"] = "curitiba-smart"
    cfg["enabled"] = False
    mgr.save_duckdns_settings(cfg)

    # Re-read
    updated = mgr.load_duckdns_settings()
    assert updated["domain"] == "curitiba-smart"
    assert updated["enabled"] is False


def test_duckdns_handler_get_config(temp_settings_file):
    mgr = DatabaseSettingsManager(settings_path=temp_settings_file)
    mock_transport = MagicMock()
    mock_transport.is_caddy_running = True
    mock_transport.caddy_port = 443

    handler = DuckDnsHandler(settings_mgr=mgr, go_transport=mock_transport)

    msg = IpcMessage(action="get_duckdns_config", payload={})
    res = handler.handle_get_duckdns_config(msg)

    assert res["status"] == "ONLINE"
    assert res["domain"] == "saopaulo-transito"
    assert res["enabled"] is True
    assert res["public_url"] == "https://saopaulo-transito.duckdns.org"
    assert res["caddy_running"] is True


def test_duckdns_handler_save_config_delegates_to_go(temp_settings_file):
    mgr = DatabaseSettingsManager(settings_path=temp_settings_file)
    mock_transport = MagicMock()
    handler = DuckDnsHandler(settings_mgr=mgr, go_transport=mock_transport)

    msg = IpcMessage(
        action="save_duckdns_config",
        payload={
            "domain": "campinas-its.duckdns.org",  # Should be normalized
            "token": "tok_xyz",
            "enabled": True,
            "caddy_enabled": True,
            "port": 8081,
            "https_port": 443,
        },
    )
    res = handler.handle_save_duckdns_config(msg)

    assert res["status"] == "ok"
    assert res["public_url"] == "https://campinas-its.duckdns.org"
    mock_transport.send_command.assert_called_once_with({
        "cmd": "SET_DUCKDNS",
        "domain": "campinas-its",
        "token": "tok_xyz",
        "port": "8081",
        "https_port": 443,
        "caddy_enabled": True,
        "enabled": True,
    })


def test_duckdns_handler_test_connection_delegates_to_go():
    mock_transport = MagicMock()
    mock_transport.test_duckdns.return_value = {
        "status": "ok",
        "message": "Conexão validada com sucesso! Latência: 45 ms.",
        "domain": "curitiba.duckdns.org",
        "latency_ms": 45,
    }

    handler = DuckDnsHandler(go_transport=mock_transport)
    msg = IpcMessage(
        action="test_duckdns_connection",
        payload={"domain": "curitiba", "token": "test-token"},
    )

    res = handler.handle_test_duckdns_connection(msg)
    assert res["status"] == "ok"
    assert res["latency_ms"] == 45
    mock_transport.test_duckdns.assert_called_once_with("curitiba", "test-token", timeout=8.0)


def test_duckdns_handler_toggle_delegates_to_go(temp_settings_file):
    mgr = DatabaseSettingsManager(settings_path=temp_settings_file)
    mock_transport = MagicMock()
    handler = DuckDnsHandler(settings_mgr=mgr, go_transport=mock_transport)

    msg = IpcMessage(action="toggle_duckdns", payload={})
    res = handler.handle_toggle_duckdns(msg)

    assert res["status"] == "ok"
    # Initial was enabled=True, so toggle makes it False
    assert res["enabled"] is False
    assert res["service_status"] == "DISCONNECTED"

    mock_transport.send_command.assert_called_once_with({
        "cmd": "SET_DUCKDNS",
        "domain": "saopaulo-transito",
        "token": "mock-token-1234",
        "port": "8081",
        "https_port": 443,
        "caddy_enabled": True,
        "enabled": False,
    })


def test_network_service_unified_endpoint_with_duckdns(temp_settings_file):
    with patch("src.database.db_settings_manager.DatabaseSettingsManager.load_duckdns_settings") as mock_load:
        mock_load.return_value = {
            "domain": "prefeitura-traffic",
            "enabled": True,
            "https_port": 443,
            "port": 8081,
        }

        info = NetworkService.get_network_info()
        assert info["duckdns_enabled"] is True
        assert info["duckdns_domain"] == "prefeitura-traffic"
        assert info["unified_endpoint"] == "https://prefeitura-traffic.duckdns.org"
        assert info["unified_host"] == "prefeitura-traffic.duckdns.org"
