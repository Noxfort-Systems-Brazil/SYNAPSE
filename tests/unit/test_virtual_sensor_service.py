# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: tests/unit/test_virtual_sensor_service.py
# Author: Gabriel Moraes
# Date: 2026-09-28

import pytest
import numpy as np
from unittest.mock import MagicMock

from src.services.virtual_sensor_service import VirtualSensorService
from src.domain.entities import DataSource, MapEdge, SourceStatus, SourceType
from src.domain.app_state import AppState
from src.factories.agent_factory import AgentFactory


@pytest.fixture
def mock_app_state():
    state = MagicMock(spec=AppState)
    state.sources = MagicMock()
    return state


@pytest.fixture
def mock_agent_factory():
    factory = MagicMock(spec=AgentFactory)
    specialist = MagicMock()
    factory.get_or_create_specialist.return_value = specialist
    return factory


def test_find_nearest_active_edge_upstream(mock_app_state, mock_agent_factory):
    """Verifies that upstream active edge is prioritized for traffic continuity."""
    service = VirtualSensorService(mock_app_state, mock_agent_factory)

    # e1: n1 -> n2, e2: n2 -> n3 (e1 is upstream of e2)
    e1 = MapEdge(id="e1", from_node="n1", to_node="n2", shape=[(0, 0), (100, 0)], lanes=2, max_speed=15.0)
    e2 = MapEdge(id="e2", from_node="n2", to_node="n3", shape=[(100, 0), (200, 0)], lanes=2, max_speed=15.0)

    all_edges = [e1, e2]
    active_edge_ids = {"e1"}

    result = service.find_nearest_active_edge(e2, all_edges, active_edge_ids)
    assert result is not None
    donor_edge, relation, _ = result
    assert donor_edge.id == "e1"
    assert relation == "upstream"


def test_find_nearest_active_edge_downstream(mock_app_state, mock_agent_factory):
    """Verifies that downstream active edge is identified when no upstream is active."""
    service = VirtualSensorService(mock_app_state, mock_agent_factory)

    # e1: n1 -> n2, e2: n2 -> n3 (e2 is downstream of e1)
    e1 = MapEdge(id="e1", from_node="n1", to_node="n2", shape=[(0, 0), (100, 0)], lanes=1, max_speed=13.89)
    e2 = MapEdge(id="e2", from_node="n2", to_node="n3", shape=[(100, 0), (200, 0)], lanes=1, max_speed=13.89)

    all_edges = [e1, e2]
    active_edge_ids = {"e2"}

    result = service.find_nearest_active_edge(e1, all_edges, active_edge_ids)
    assert result is not None
    donor_edge, relation, _ = result
    assert donor_edge.id == "e2"
    assert relation == "downstream"


def test_impute_traffic_continuity_lane_scaling(mock_app_state, mock_agent_factory):
    """Verifies that traffic flow scales proportionally with lane capacity."""
    service = VirtualSensorService(mock_app_state, mock_agent_factory)

    # e_donor: 1 lane, e_target: 3 lanes
    e_donor = MapEdge(id="e_donor", from_node="n1", to_node="n2", shape=[(0, 0), (100, 0)], lanes=1, max_speed=16.0)
    e_target = MapEdge(id="e_target", from_node="n2", to_node="n3", shape=[(100, 0), (200, 0)], lanes=3, max_speed=14.0)

    all_edges = [e_donor, e_target]
    active_edge_ids = {"e_donor"}

    # Mock sensor on e_donor with 0.3 veh/s flow and 20.0 m/s speed
    src_donor = DataSource(
        id="src_donor",
        name="Donor Sensor",
        status=SourceStatus.ACTIVE,
        latest_value=0.3,
        semantic_type="Vehicle Flow",
        inferred_unit="veh/s"
    )
    mock_app_state.get_sources_associated_with_element.return_value = ["src_donor"]
    mock_app_state.get_data_source.return_value = src_donor

    imputed = service.impute_traffic_for_edge(e_target, all_edges, active_edge_ids)

    # Expected flow: 0.3 * (3 lanes / 1 lane) = 0.9 veh/s
    assert imputed["flow_vps"] == pytest.approx(0.9, rel=1e-2)
    # Expected speed capped at target max_speed: min(13.89 default or 14.0, 20.0) -> 14.0 m/s
    assert imputed["speed_ms"] <= 14.0
    assert imputed["donor_edge_id"] == "e_donor"


def test_create_or_get_virtual_sensor_bypasses_quarantine(mock_app_state, mock_agent_factory):
    """Verifies that virtual sensors are directly created as ACTIVE, bypassing Quarantine."""
    service = VirtualSensorService(mock_app_state, mock_agent_factory)
    mock_app_state.get_data_source.return_value = None

    source, specialist = service.create_or_get_virtual_sensor("edge_xyz")

    assert source.id == "virt_edge_xyz"
    assert source.status == SourceStatus.ACTIVE  # Zero-Trust bypassed for deterministic virtual sensors
    assert source.metadata.get("is_virtual") is True
    assert source.semantic_type == "Vehicle Flow"
    assert source.inferred_unit == "veh/s"

    mock_app_state.add_data_source.assert_called_once_with(source)
    mock_app_state.sources.associate.assert_called_once_with("virt_edge_xyz", "edge_xyz")
    mock_agent_factory.get_or_create_specialist.assert_called_once_with("virt_edge_xyz")
    assert specialist.target_edge_id == "edge_xyz"


def test_sync_virtual_sensors_covers_unobserved_edges(mock_app_state, mock_agent_factory):
    """Verifies that sync_virtual_sensors populates all edges lacking physical sensors."""
    service = VirtualSensorService(mock_app_state, mock_agent_factory)

    e_phys = MapEdge(id="edge_phys", from_node="n1", to_node="n2", shape=[(0, 0), (100, 0)], lanes=2, max_speed=13.89)
    e_virt = MapEdge(id="edge_unmonitored", from_node="n2", to_node="n3", shape=[(100, 0), (200, 0)], lanes=2, max_speed=13.89)

    mock_app_state.get_all_edges.return_value = [e_phys, e_virt]

    # Active physical sensor on edge_phys
    src_phys = DataSource(id="src_p1", name="Loop Detector", status=SourceStatus.ACTIVE, latest_value=0.4, metadata={"is_virtual": False})
    mock_app_state.get_all_data_sources.return_value = [src_phys]
    mock_app_state.get_element_for_source.side_effect = lambda sid: "edge_phys" if sid == "src_p1" else None
    mock_app_state.get_data_source.return_value = None

    results = service.sync_virtual_sensors()

    assert "edge_unmonitored" in results
    assert "edge_phys" not in results
    assert results["edge_unmonitored"]["flow_vps"] > 0
