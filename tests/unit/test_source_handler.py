# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: tests/unit/test_source_handler.py

import pytest
from src.handlers.source_handler import SourceCommandHandler
from src.domain.app_state import AppState
from src.ipc.ipc_protocol import IpcMessage


def test_handle_add_source_with_location_association(monkeypatch):
    """Verify handle_add_source associates sensor with street and returns location."""
    monkeypatch.setattr(
        "src.database.db_settings_manager.DatabaseSettingsManager.load_duckdns_settings",
        lambda self: {"enabled": True, "domain": "test-sensor.duckdns.org", "token": "test-token"}
    )
    app_state = AppState()
    handler = SourceCommandHandler(app_state=app_state)

    msg = IpcMessage(
        action="add_source",
        payload={
            "id": "src_manual_1",
            "name": "Radar Av. Paulista",
            "is_local": True,
            "connection": "http://127.0.0.1:8081/src_manual_1",
            "location": "edge_paulista_1",
        }
    )

    response = handler.handle_add_source(msg)

    assert response["id"] == "src_manual_1"
    assert response["name"] == "Radar Av. Paulista"
    assert response["is_local"] is True
    assert response["associated_element"] == "edge_paulista_1"

    # Verify association was recorded in app_state
    associated = app_state.sources.get_element_for_source("src_manual_1")
    assert associated == "edge_paulista_1"


def test_handle_add_source_without_location():
    """Verify handle_add_source succeeds even when no location is provided."""
    app_state = AppState()
    handler = SourceCommandHandler(app_state=app_state)

    msg = IpcMessage(
        action="add_source",
        payload={
            "id": "src_manual_2",
            "name": "Feed Global Waze",
            "is_local": False,
            "connection": "https://api.waze.com/traffic",
        }
    )

    response = handler.handle_add_source(msg)

    assert response["id"] == "src_manual_2"
    assert response["is_local"] is False
    assert response["associated_element"] is None


def test_handle_update_source_success(monkeypatch):
    """Verify handle_update_source modifies sensor attributes and re-associates element."""
    monkeypatch.setattr(
        "src.database.db_settings_manager.DatabaseSettingsManager.load_duckdns_settings",
        lambda self: {"enabled": True, "domain": "test-sensor.duckdns.org", "token": "test-token"}
    )
    app_state = AppState()
    handler = SourceCommandHandler(app_state=app_state)

    # 1. Add sensor initially
    add_msg = IpcMessage(
        action="add_source",
        payload={
            "id": "src_edit_1",
            "name": "Camera 1",
            "is_local": True,
            "connection": "http://127.0.0.1:8081/src_edit_1",
            "location": "edge_a",
        }
    )
    handler.handle_add_source(add_msg)

    # 2. Update sensor: rename and associate to new edge
    update_msg = IpcMessage(
        action="update_source",
        payload={
            "id": "src_edit_1",
            "name": "Camera Central Norte",
            "is_local": True,
            "connection": "http://192.168.1.50:8081/src_edit_1",
            "location": "edge_b",
        }
    )
    res = handler.handle_update_source(update_msg)

    assert res["success"] is True
    assert res["id"] == "src_edit_1"
    assert res["name"] == "Camera Central Norte"
    assert res["associated_element"] == "edge_b"

    # Verify state in repository
    source = app_state.sources.get("src_edit_1")
    assert source.name == "Camera Central Norte"
    assert source.connection_string == "http://192.168.1.50:8081/src_edit_1"
    assert app_state.sources.get_element_for_source("src_edit_1") == "edge_b"


def test_handle_update_source_disassociate(monkeypatch):
    """Verify handle_update_source can disassociate a local sensor from an element."""
    monkeypatch.setattr(
        "src.database.db_settings_manager.DatabaseSettingsManager.load_duckdns_settings",
        lambda self: {"enabled": True, "domain": "test-sensor.duckdns.org", "token": "test-token"}
    )
    app_state = AppState()
    handler = SourceCommandHandler(app_state=app_state)

    # Add local sensor with location
    add_msg = IpcMessage(
        action="add_source",
        payload={
            "id": "src_edit_2",
            "name": "Local Traffic Sensor",
            "is_local": True,
            "connection": "http://127.0.0.1:8081/src_edit_2",
            "location": "edge_c",
        }
    )
    handler.handle_add_source(add_msg)
    assert app_state.sources.get_element_for_source("src_edit_2") == "edge_c"

    # Update with empty location to disassociate
    update_msg = IpcMessage(
        action="update_source",
        payload={
            "id": "src_edit_2",
            "name": "Local Traffic Sensor Disassociated",
            "location": "",
        }
    )
    res = handler.handle_update_source(update_msg)

    assert res["success"] is True
    assert res["name"] == "Local Traffic Sensor Disassociated"
    assert app_state.sources.get_element_for_source("src_edit_2") is None


def test_handle_update_source_not_found():
    """Verify handle_update_source raises ValueError if source does not exist."""
    app_state = AppState()
    handler = SourceCommandHandler(app_state=app_state)

    update_msg = IpcMessage(
        action="update_source",
        payload={
            "id": "src_non_existent",
            "name": "Unknown",
        }
    )
    with pytest.raises(ValueError, match="não encontrado"):
        handler.handle_update_source(update_msg)

