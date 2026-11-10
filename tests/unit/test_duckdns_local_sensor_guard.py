# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
from unittest.mock import MagicMock, patch

from src.domain.app_state import AppState
from src.domain.entities import DataSource, SourceType, SourceStatus
from src.handlers.source_handler import SourceCommandHandler
from src.ipc.ipc_protocol import IpcMessage
from src.phases.runtime_phase import RuntimePhase


def test_add_local_source_rejected_when_duckdns_disabled(monkeypatch):
    """Local sensor registration must be strictly rejected if DuckDNS is disabled."""
    monkeypatch.setattr(
        "src.database.db_settings_manager.DatabaseSettingsManager.load_duckdns_settings",
        lambda self: {"enabled": False, "domain": "traffic-sp.duckdns.org", "token": "abc"}
    )
    app_state = AppState()
    handler = SourceCommandHandler(app_state=app_state)

    msg = IpcMessage(
        action="add_source",
        payload={
            "id": "cam_loc_01",
            "name": "Camera Av Paulista",
            "is_local": True,
            "connection": "http://127.0.0.1:8081/cam_loc_01",
        }
    )

    with pytest.raises(ValueError, match="DuckDNS Obrigatório"):
        handler.handle_add_source(msg)


def test_add_local_source_rejected_when_duckdns_domain_empty(monkeypatch):
    """Local sensor registration must be rejected if DuckDNS is enabled but domain is empty."""
    monkeypatch.setattr(
        "src.database.db_settings_manager.DatabaseSettingsManager.load_duckdns_settings",
        lambda self: {"enabled": True, "domain": "   ", "token": "abc"}
    )
    app_state = AppState()
    handler = SourceCommandHandler(app_state=app_state)

    msg = IpcMessage(
        action="add_source",
        payload={
            "id": "cam_loc_02",
            "name": "Radar Marginal Tiete",
            "is_local": True,
            "connection": "http://127.0.0.1:8081/cam_loc_02",
        }
    )

    with pytest.raises(ValueError, match="DuckDNS Obrigatório"):
        handler.handle_add_source(msg)


def test_add_local_source_allowed_when_duckdns_active(monkeypatch):
    """Local sensor registration succeeds when DuckDNS is enabled with a valid domain."""
    monkeypatch.setattr(
        "src.database.db_settings_manager.DatabaseSettingsManager.load_duckdns_settings",
        lambda self: {"enabled": True, "domain": "traffic-sp.duckdns.org", "token": "valid-token"}
    )
    app_state = AppState()
    handler = SourceCommandHandler(app_state=app_state)

    msg = IpcMessage(
        action="add_source",
        payload={
            "id": "cam_loc_03",
            "name": "Radar 23 de Maio",
            "is_local": True,
            "connection": "https://traffic-sp.duckdns.org/cam_loc_03",
        }
    )

    response = handler.handle_add_source(msg)
    assert response["id"] == "cam_loc_03"
    assert response["is_local"] is True
    assert app_state.sources.get("cam_loc_03") is not None


def test_add_global_source_allowed_even_without_duckdns(monkeypatch):
    """Global (cloud) sensors do not require DuckDNS and can always be registered."""
    monkeypatch.setattr(
        "src.database.db_settings_manager.DatabaseSettingsManager.load_duckdns_settings",
        lambda self: {"enabled": False, "domain": "", "token": ""}
    )
    app_state = AppState()
    handler = SourceCommandHandler(app_state=app_state)

    msg = IpcMessage(
        action="add_source",
        payload={
            "id": "feed_global_01",
            "name": "TomTom Live Feed",
            "is_local": False,
            "connection": "https://api.tomtom.com/traffic",
        }
    )

    response = handler.handle_add_source(msg)
    assert response["id"] == "feed_global_01"
    assert response["is_local"] is False
    assert app_state.sources.get("feed_global_01") is not None


def test_batch_import_rejected_when_duckdns_inactive(monkeypatch):
    """Batch import of local sensors returns error result when DuckDNS is inactive."""
    monkeypatch.setattr(
        "src.database.db_settings_manager.DatabaseSettingsManager.load_duckdns_settings",
        lambda self: {"enabled": False, "domain": "", "token": ""}
    )
    app_state = AppState()
    handler = SourceCommandHandler(app_state=app_state)

    msg = IpcMessage(
        action="import_batch_sources",
        payload={
            "csv_content": "id,name,location,fps,resolution\nloc_1,Cam1,edge_1,15,1080p",
            "host": "127.0.0.1",
            "port": 8081,
        }
    )

    result = handler.handle_import_batch_sources(msg)
    assert result["success"] is False
    assert result["imported_count"] == 0
    assert any("DuckDNS Obrigatório" in err for err in result["errors"])


def test_batch_import_allowed_when_duckdns_active(monkeypatch):
    """Batch import proceeds when DuckDNS is active."""
    monkeypatch.setattr(
        "src.database.db_settings_manager.DatabaseSettingsManager.load_duckdns_settings",
        lambda self: {"enabled": True, "domain": "traffic-sp.duckdns.org", "token": "tok"}
    )
    app_state = AppState()
    handler = SourceCommandHandler(app_state=app_state)

    fake_import_result = {
        "success": True,
        "imported_count": 2,
        "items": [],
        "errors": []
    }

    with patch("src.services.sensor_batch_service.SensorBatchService.import_manifest", return_value=fake_import_result):
        msg = IpcMessage(
            action="import_batch_sources",
            payload={
                "csv_content": "csv_data",
                "host": "traffic-sp.duckdns.org",
                "port": 443,
            }
        )
        result = handler.handle_import_batch_sources(msg)
        assert result["success"] is True
        assert result["imported_count"] == 2


def test_runtime_phase_aborts_when_local_sensor_present_and_duckdns_inactive(monkeypatch):
    """RuntimePhase.start must abort if active local sensor exists without configured DuckDNS."""
    monkeypatch.setattr(
        "src.database.db_settings_manager.DatabaseSettingsManager.load_duckdns_settings",
        lambda self: {"enabled": False, "domain": "", "token": ""}
    )
    app_state = AppState()
    local_src = DataSource(
        id="loc_10",
        name="Radar 10",
        source_type=SourceType.API,
        connection_string="http://127.0.0.1:8081/loc_10",
        is_local=True,
        status=SourceStatus.ACTIVE,
    )
    global_src = DataSource(
        id="glob_10",
        name="Global API",
        source_type=SourceType.API,
        connection_string="https://api.waze.com",
        is_local=False,
        status=SourceStatus.ACTIVE,
    )
    app_state.add_data_source(local_src)
    app_state.add_data_source(global_src)

    phase = RuntimePhase(app_state, MagicMock())
    started = phase.start()

    assert started is False


def test_runtime_phase_proceeds_when_duckdns_active(monkeypatch):
    """RuntimePhase.start proceeds when DuckDNS is active for local sensors."""
    monkeypatch.setattr(
        "src.database.db_settings_manager.DatabaseSettingsManager.load_duckdns_settings",
        lambda self: {"enabled": True, "domain": "traffic-sp.duckdns.org", "token": "tok"}
    )
    app_state = AppState()
    local_src = DataSource(
        id="loc_20",
        name="Radar 20",
        source_type=SourceType.API,
        connection_string="https://traffic-sp.duckdns.org/loc_20",
        is_local=True,
        status=SourceStatus.ACTIVE,
    )
    global_src = DataSource(
        id="glob_20",
        name="Global API",
        source_type=SourceType.API,
        connection_string="https://api.waze.com",
        is_local=False,
        status=SourceStatus.ACTIVE,
    )
    app_state.add_data_source(local_src)
    app_state.add_data_source(global_src)

    phase = RuntimePhase(app_state, MagicMock())
    with patch.object(phase.launcher, "start_engines"), \
         patch.object(phase.connector, "start_connection"):
        started = phase.start()
        assert started is True
