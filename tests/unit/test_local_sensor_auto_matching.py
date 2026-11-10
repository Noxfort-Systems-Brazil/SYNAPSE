# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import json
from datetime import datetime, date
import numpy as np
import pytest
from unittest.mock import MagicMock

from src.domain.entities import DataSource, SourceType, SourceStatus, MapEdge
from src.domain.app_state import AppState
from src.managers.graph_manager import GraphManager
from src.linguist.local_topology_matcher import LocalTopologyMatcher
from src.utils.debug_logger import JsonLinesLogger


def test_json_lines_logger_handles_numpy_types(tmp_path, monkeypatch):
    """Verifies that JsonLinesLogger serializes numpy arrays, scalars, and datetimes without error."""
    monkeypatch.setattr("src.utils.debug_logger.get_log_dir", lambda: tmp_path)

    logger = JsonLinesLogger("test_subfolder", "numpy_test")
    test_record = {
        "embedding": np.array([0.1, 0.25, 0.99], dtype=np.float32),
        "scalar_float": np.float32(12.34),
        "scalar_int": np.int64(999),
        "scalar_bool": np.bool_(True),
        "timestamp": datetime(2026, 9, 29, 12, 0, 0),
        "date_field": date(2026, 9, 29),
    }

    # Should not raise TypeError: Object of type ndarray is not JSON serializable or NameError
    logger.log(test_record)
    logger.close()

    assert logger.file_path is not None and logger.file_path.exists()

    with open(logger.file_path, "r", encoding="utf-8") as f:
        line = f.readline().strip()

    assert len(line) > 0
    loaded = json.loads(line)
    assert loaded["embedding"] == [pytest.approx(0.1, 1e-4), pytest.approx(0.25, 1e-4), pytest.approx(0.99, 1e-4)]
    assert abs(loaded["scalar_float"] - 12.34) < 1e-4
    assert loaded["scalar_int"] == 999
    assert loaded["scalar_bool"] is True
    assert "2026-09-29T12:00:00" in loaded["timestamp"]
    assert "2026-09-29" in loaded["date_field"]


def test_local_topology_matcher_extracts_coordinates_from_data_chunk(monkeypatch):
    """Verifies that LocalTopologyMatcher extracts coordinates from data_chunk when source.metadata lacks them."""
    app_state = MagicMock(spec=AppState)

    # Edge located at x=100..110, y=100
    edge = MapEdge(
        id="nearby_edge#0",
        from_node="n1",
        to_node="n2",
        shape=[(90.0, 100.0), (110.0, 100.0)],
        lanes=1,
        length=20.0,
        max_speed=13.89,
    )
    app_state.get_element_for_source.return_value = None
    app_state.get_edge.return_value = None
    app_state.get_all_edges.return_value = [edge]
    app_state.get_map_source_path.return_value = None

    matcher = LocalTopologyMatcher(app_state)

    # Source has no coordinates in metadata
    source = DataSource(
        id="loop_unconfigured",
        name="Unconfigured Loop",
        source_type=SourceType.MQTT,
        is_local=True,
        metadata={},
    )

    # Data chunk contains GPS coordinates; mock the polyline extractor to project to (100.0, 100.0)
    chunk = [
        {"sensor_id": "loop_unconfigured", "lat": -23.5505, "lon": -46.6333, "speed_kmh": 40.0}
    ]

    mock_extractor = MagicMock()
    mock_extractor.extract.return_value = [(100.0, 100.0)]
    monkeypatch.setattr("src.pipeline.global_polyline_extractor.GlobalPolylineExtractor", lambda: mock_extractor)

    # Mock projection service to return (100.0, 100.0)
    mock_proj = MagicMock()
    mock_proj.project.return_value = [(100.0, 100.0)]
    monkeypatch.setattr("src.services.geo_projection_service.get_projection_service_for_map", lambda path: mock_proj)

    candidates = matcher.find_candidates(source, data_chunk=chunk)
    assert len(candidates) > 0
    assert candidates[0].id == "nearby_edge#0"


def test_graph_manager_camera_recognition_dynamic_speed():
    """Verifies that GraphManager extracts vehicle speed from camera recognition packets and dynamically updates edge state."""
    app_state = AppState()
    gm = GraphManager(app_state=app_state)

    gm.nodes["nA"] = MagicMock()
    gm.nodes["nB"] = MagicMock()
    gm.ordered_node_ids = ["nA", "nB"]

    gm.edge_elements_map = {
        "edge_camera_lane": {
            "from": "nA",
            "to": "nB",
            "speed": 13.89,  # ~50 km/h
            "lanes": 2,
            "length": 100.0,
        }
    }

    app_state.sources.associate("cam_entry", "edge_camera_lane")

    # Raw payload with vehicle recognitions containing estimated_speed_kmh
    recognition_payload = {
        "data": [
            {"plate": "BRA2E19", "confidence": 0.95, "estimated_speed_kmh": 36.0},
            {"plate": "XYZ9876", "confidence": 0.92, "estimated_speed_kmh": 54.0},
        ]
    }

    # 36 km/h and 54 km/h average to 45 km/h = 12.5 m/s
    gm.update_node_memory("cam_entry", 2.0, raw_payload=recognition_payload)

    edge_data = gm.edge_elements_map["edge_camera_lane"]
    assert abs(edge_data["speed"] - 12.5) < 0.1
    # Density should be dynamically calculated from Greenshields model
    assert edge_data["density"] > 0.0


def test_graph_manager_dict_speed_and_flow_payload():
    """Verifies that GraphManager handles dict payloads with speed_kmh and flow keys respecting road geometry."""
    app_state = AppState()
    gm = GraphManager(app_state=app_state)

    gm.nodes["n1"] = MagicMock()
    gm.nodes["n2"] = MagicMock()
    gm.ordered_node_ids = ["n1", "n2"]

    # Road with max speed of 22.22 m/s (~80 km/h)
    gm.edge_elements_map = {
        "sensor_edge": {
            "from": "n1",
            "to": "n2",
            "speed": 22.22,  # 80 km/h
            "lanes": 1,
            "length": 200.0,
        }
    }

    app_state.sources.associate("telemetry_sensor", "sensor_edge")

    # Sensor reports 72.0 km/h (20.0 m/s), within 80 km/h max speed
    payload = {"speed_kmh": 72.0, "flow": 450}
    gm.update_node_memory("telemetry_sensor", payload, raw_payload=payload)

    edge_data = gm.edge_elements_map["sensor_edge"]
    # 72 km/h / 3.6 = 20.0 m/s
    assert abs(edge_data["speed"] - 20.0) < 0.1
    assert edge_data["density"] > 0.0
