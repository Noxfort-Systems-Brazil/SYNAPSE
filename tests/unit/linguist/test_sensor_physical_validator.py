# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
import numpy as np
from unittest.mock import MagicMock

from src.physics.sensor_physical_validator import SensorPhysicalValidator
from src.domain.app_state import AppState
from src.domain.entities import DataSource, SourceType, MapEdge


def test_sensor_physical_validator_modality():
    """Verifies that SensorPhysicalValidator validates counts and speeds appropriately."""
    validator = SensorPhysicalValidator()
    src_cam = DataSource(id="c1", name="Camera 1", source_type=SourceType.API, is_local=True)

    assert validator.validate(src_cam, np.array([0.0, 3.0, 2.0, 0.0])) is True
    assert validator.validate(src_cam, np.array([-1.0, 2.0])) is False
    assert validator.validate(src_cam, np.array([999.0])) is False


def test_sensor_physical_validator_dynamic_topology():
    """Verifies that SensorPhysicalValidator adapts flow thresholds according to road lanes."""
    app_state = MagicMock(spec=AppState)
    validator = SensorPhysicalValidator(app_state=app_state)

    edge_1lane = MapEdge(id="edge_res", from_node="n1", to_node="n2", shape=[], lanes=1, max_speed=13.89)
    edge_5lanes = MapEdge(id="edge_hwy", from_node="n3", to_node="n4", shape=[], lanes=5, max_speed=25.0)

    src_res = DataSource(id="src_flow_res", name="Radar Rua Residencial", source_type=SourceType.API)
    src_hwy = DataSource(id="src_flow_hwy", name="Radar Marginal Tietê", source_type=SourceType.API)

    app_state.get_element_for_source.side_effect = lambda sid: "edge_res" if sid == "src_flow_res" else "edge_hwy"
    app_state.get_edge.side_effect = lambda eid: edge_1lane if eid == "edge_res" else edge_5lanes

    assert validator.validate(src_res, np.array([4500.0]), [{"flow": 4500.0}]) is False
    assert validator.validate(src_hwy, np.array([4500.0]), [{"flow": 4500.0}]) is True


def test_sensor_physical_validator_dynamic_speed_limit():
    """Verifies that SensorPhysicalValidator respects posted edge max speed with reasonable overrun."""
    app_state = MagicMock(spec=AppState)
    validator = SensorPhysicalValidator(app_state=app_state)

    edge_50 = MapEdge(id="edge_50", from_node="n1", to_node="n2", shape=[], lanes=2, max_speed=13.89)
    src_speed = DataSource(id="src_spd", name="Radar Av Paulista", source_type=SourceType.API)

    app_state.get_element_for_source.return_value = "edge_50"
    app_state.get_edge.return_value = edge_50

    assert validator.validate(src_speed, np.array([60.0]), [{"speed": 60.0}]) is True
    assert validator.validate(src_speed, np.array([130.0]), [{"speed": 130.0}]) is False


def test_sensor_physical_validator_dynamic_delta_time_counts():
    """Verifies that vehicle count threshold dynamically scales with sampling dt."""
    validator = SensorPhysicalValidator()
    src = DataSource(id="cam_sp", name="Camera SP", source_type=SourceType.API)

    chunk_1s = [{"time": 100.0, "count": 200}, {"time": 101.0, "count": 200}]
    assert validator.validate(src, np.array([200.0]), chunk_1s) is False

    chunk_5m = [{"time": 100.0, "count": 200}, {"time": 400.0, "count": 200}]
    assert validator.validate(src, np.array([200.0]), chunk_5m) is True


def test_sensor_physical_validator_offpeak_empty_street():
    """Verifies that quiet streets at night with 0 vehicles are NOT falsely flagged as dead sensors."""
    validator = SensorPhysicalValidator()
    src_cam = DataSource(id="cam_empty", name="Camera Madrugada", source_type=SourceType.API)

    empty_series = np.zeros(20, dtype=np.float32)
    assert validator.validate(src_cam, empty_series) is True


def test_sensor_physical_validator_kinematic_acceleration_rejection():
    """Verifies that impossible vehicle acceleration jumps are caught and rejected."""
    validator = SensorPhysicalValidator()
    src_speed = DataSource(id="radar_accel", name="Radar Speed", source_type=SourceType.API)

    chunk = [{"time": 10.0, "speed": 10.0}, {"time": 10.5, "speed": 100.0}]
    telemetry = np.array([10.0, 100.0])
    assert validator.validate(src_speed, telemetry, chunk) is False
