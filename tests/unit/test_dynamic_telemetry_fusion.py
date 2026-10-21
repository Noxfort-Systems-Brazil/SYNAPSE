# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: tests/unit/test_dynamic_telemetry_fusion.py

import pytest
import numpy as np
import torch
from unittest.mock import MagicMock

from src.domain.entities import DataSource, SourceType, SourceStatus, MapNode, MapEdge
from src.domain.app_state import AppState
from src.managers.graph_manager import GraphManager
from src.meh.edge_payload_formatter import EdgePayloadFormatter
from src.engine.tensor_builder import TensorBuilder
from src.managers.kse_manager import KSEManager


def test_graph_manager_dynamic_density_no_static_clamp():
    """Verifies that GraphManager updates node memory with dynamic continuum density rather than a 15.0 clamp."""
    app_state = AppState()
    gm = GraphManager(app_state=app_state)
    
    gm.nodes["node_u"] = MagicMock()
    gm.nodes["node_v"] = MagicMock()
    gm.ordered_node_ids = ["node_u", "node_v"]
    
    gm.edge_elements_map = {
        "edge_main": {
            "from": "node_u",
            "to": "node_v",
            "speed": 16.67,  # ~60 km/h
            "lanes": 2,
            "length": 150.0,
        }
    }
    
    app_state.sources.associate("src_speed", "edge_main")
    
    # Ingest speed of 10.0 m/s (~36 km/h)
    gm.update_node_memory("src_speed", 10.0, raw_payload={"speed_kmh": 36.0})
    
    edge_data = gm.edge_elements_map["edge_main"]
    assert edge_data["speed"] == 10.0
    
    # Under Greenshields: k = k_jam * (1 - v / v_free)
    # With v_free = 16.67, v = 10.0, ratio = 1 - 10/16.67 ≈ 0.4
    # Jam density for 1 lane = 140. k ≈ 140 * 0.4 ≈ 56.0 veh/km != flat 15.0!
    assert edge_data["density"] > 15.0
    assert abs(edge_data["density"] - 56.0) < 1.0


def test_graph_manager_bidirectional_association_updates():
    """Verifies that a sensor associated to both forward and reverse edges updates both."""
    app_state = AppState()
    gm = GraphManager(app_state=app_state)
    
    gm.nodes["n1"] = MagicMock()
    gm.nodes["n2"] = MagicMock()
    gm.nodes["n3"] = MagicMock()
    gm.ordered_node_ids = ["n1", "n2", "n3"]
    
    gm.edge_elements_map = {
        "-370320174#4": {"from": "n1", "to": "n2", "speed": 13.89, "lanes": 1, "length": 80.0},
        "370320174#4": {"from": "n2", "to": "n3", "speed": 13.89, "lanes": 1, "length": 80.0},
    }
    
    app_state.sources.associate("src_loop", "-370320174#4")
    app_state.sources.associate("src_loop", "370320174#4")
    
    gm.update_node_memory("src_loop", 8.33, raw_payload={"speed_kmh": 30.0})
    
    assert gm.edge_elements_map["-370320174#4"]["speed"] == 8.33
    assert gm.edge_elements_map["370320174#4"]["speed"] == 8.33


def test_edge_payload_formatter_macro_speed_and_baseline_density():
    """Verifies that EdgePayloadFormatter uses associated sensor data and macroscopic speed baseline."""
    app_state = AppState()
    
    global_src = DataSource(
        id="tomtom_api",
        name="TomTom API",
        source_type=SourceType.API,
        is_local=False,
        latest_value=12.5,
        status=SourceStatus.ACTIVE,
    )
    app_state.add_data_source(global_src)
    
    # Add an unobserved edge to topology
    edge = MapEdge(
        id="unobserved_edge",
        from_node="n1",
        to_node="n2",
        shape=[(0.0, 0.0), (0.0, 1.0)],
        max_speed=16.67,
        lanes=1,
        length=100.0,
    )
    app_state.topology._edges["unobserved_edge"] = edge
    
    # Pass flat_data with no specific reading for this edge
    payload = EdgePayloadFormatter.format_edge_payload(
        flat_data={"other_sensor": 10.0},
        app_state=app_state,
    )
    
    assert "unobserved_edge" in payload
    edge_payload = payload["unobserved_edge"]
    assert edge_payload["speed"] == 12.5
    # Density should be calculated from Greenshields with macro speed, not flat 15.0
    assert edge_payload["density"] != 15.0
    assert edge_payload["occupancy"] != pytest.approx(15.0 / 140.0, rel=1e-3)


def test_tensor_builder_observability_mask_and_global_velocities():
    """Verifies that TensorBuilder sets mask_list and extracts global macroscopic velocities."""
    app_state = AppState()
    global_src = DataSource(
        id="waze_api",
        name="Waze API",
        source_type=SourceType.API,
        is_local=False,
        latest_value=15.0,
        status=SourceStatus.ACTIVE,
    )
    app_state.add_data_source(global_src)
    
    gm = GraphManager(app_state=app_state)
    mock_n1 = MagicMock()
    mock_n1.memory.get_numpy.return_value = np.zeros(60)
    mock_n2 = MagicMock()
    mock_n2.memory.get_numpy.return_value = np.zeros(60)
    gm.nodes = {"n_live": mock_n1, "n_virtual": mock_n2}
    gm.ordered_node_ids = ["n_live", "n_virtual"]
    
    tb = TensorBuilder(device=torch.device("cpu"), coordinator_model=None, graph_manager=gm)
    
    snapshot = {
        "n_live": {"type": "real", "status": "Active", "value": 11.2},
        "n_virtual": {"type": "virtual", "status": "Synthesized", "value": 0.0},
    }
    
    x_spatial, edge_index, x_temporal, mask, global_vel = tb.prepare_tensors(snapshot)
    
    assert mask.shape == (2,)
    ordered_ids = gm.get_ordered_node_ids()
    live_idx = ordered_ids.index("n_live")
    virt_idx = ordered_ids.index("n_virtual")
    
    assert mask[live_idx].item() == 1.0
    assert mask[virt_idx].item() == 0.0
    
    assert global_vel[0].item() == 15.0
    assert global_vel[1].item() == 15.0


def test_kse_manager_sensor_timeout_threshold():
    """Verifies that KSEManager uses 3.0s timeout to tolerate neural cycle heartbeat."""
    app_state = AppState()
    kse = KSEManager(app_state=app_state)
    assert kse.sensor_timeout_threshold == 3.0


def test_waze_multi_jam_unpacking_and_hierarchy_interpolation():
    """Verifies that multi-segment Waze jams unpack onto distinct edges and road hierarchy prevents pasteurization."""
    from src.physics.traffic_hydrodynamics import TrafficHydrodynamicEngine

    app_state = AppState()
    nodes_data = [
        {"id": "n1", "x": 0.0, "y": 0.0, "type": "traffic_light"},
        {"id": "n2", "x": 100.0, "y": 0.0, "type": "traffic_light"},
        {"id": "n3", "x": 200.0, "y": 0.0, "type": "priority"},
        {"id": "n4", "x": 100.0, "y": 100.0, "type": "priority"},
    ]
    edges_data = [
        {
            "id": "e_jam_1",
            "from": "n1",
            "to": "n2",
            "shape": [(0.0, 0.0), (100.0, 0.0)],
            "length": 100.0,
            "max_speed": 13.89,
            "lanes": 2,
            "edge_type": "highway.secondary",
            "priority": 11,
        },
        {
            "id": "e_arterial_extrap",
            "from": "n2",
            "to": "n3",
            "shape": [(100.0, 0.0), (200.0, 0.0)],
            "length": 100.0,
            "max_speed": 13.89,
            "lanes": 2,
            "edge_type": "highway.secondary",
            "priority": 11,
        },
        {
            "id": "e_residential_extrap",
            "from": "n2",
            "to": "n4",
            "shape": [(100.0, 0.0), (100.0, 100.0)],
            "length": 120.0,
            "max_speed": 13.89,
            "lanes": 1,
            "edge_type": "highway.residential",
            "priority": 3,
        },
    ]
    app_state.set_map_data(nodes_data, edges_data)
    gm = GraphManager(app_state=app_state, embedding_dim=16)

    waze_payload = {
        "jams": [
            {
                "speedKMH": 7.2,
                "line": [{"x": 0.0, "y": 0.0}, {"x": 100.0, "y": 0.0}],
            }
        ]
    }
    gm.update_node_memory("waze_global", 1.0, raw_payload=waze_payload)

    assert "e_jam_1" in gm.direct_edge_metrics
    assert abs(gm.direct_edge_metrics["e_jam_1"]["speed"] - 2.0) < 0.1
    assert gm.direct_edge_metrics["e_jam_1"]["density"] > 100.0

    # Connected node n2 must have received the continuum density (> 100), not raw 1.0
    assert gm.nodes["n2"].last_value > 100.0

    # Compare interpolated arterial vs residential street from the same junction n2
    snap = {
        "n2": {"value": gm.nodes["n2"].last_value, "type": "real", "status": "Active"},
        "n3": {"value": 15.0, "type": "synthetic", "status": "Ghost"},
        "n4": {"value": 15.0, "type": "synthetic", "status": "Ghost"},
    }
    d_art, _ = TrafficHydrodynamicEngine.resolve_edge_state(app_state.get_edge("e_arterial_extrap"), snap)
    d_res, _ = TrafficHydrodynamicEngine.resolve_edge_state(app_state.get_edge("e_residential_extrap"), snap)
    assert d_art > d_res * 1.5


def test_alias_device_id_routing_and_historical_jam_isolation():
    """Verifies that external alias device IDs (e.g. loop_01 -> src_2) resolve to canonical IDs and update direct_edge_metrics, and localized global jam sources do not contaminate HISTORICAL fallback."""
    from src.pipeline.ingestion_pipeline import IngestionPipeline
    from src.adapters.ingestion_hub import IngestionHub
    from src.engine.data_flow_router import DataFlowRouter

    app_state = AppState()
    loop_src = DataSource(
        id="src_2",
        name="Loop",
        source_type=SourceType.MQTT,
        connection_string="https://noxfortsynapse.duckdns.org:8443/src_2",
        is_local=True,
        status=SourceStatus.ACTIVE,
        semantic_type="Vehicle Count",
        metadata={"conversion_rule": 5},
    )
    waze_src = DataSource(
        id="api_global_gius8",
        name="waze",
        source_type=SourceType.API,
        connection_string="http://localhost:8088/api/waze/feed",
        is_local=False,
        status=SourceStatus.ACTIVE,
        latest_value=1.0,
        metadata={"extraction_path": ["jams"], "extraction_mode": "detection_list"},
    )
    app_state.add_data_source(loop_src)
    app_state.add_data_source(waze_src)

    nodes_data = [
        {"id": "n1", "x": 0.0, "y": 0.0, "type": "priority"},
        {"id": "n2", "x": 243.0, "y": 0.0, "type": "priority"},
        {"id": "n3", "x": 500.0, "y": 0.0, "type": "priority"},
    ]
    edges_data = [
        {
            "id": "-370320174#4",
            "from": "n1",
            "to": "n2",
            "shape": [(0.0, 0.0), (243.0, 0.0)],
            "length": 243.47,
            "max_speed": 27.78,
            "lanes": 1,
            "edge_type": "highway.secondary",
            "priority": 11,
        },
        {
            "id": "-103342059#0",
            "from": "n2",
            "to": "n3",
            "shape": [(243.0, 0.0), (500.0, 0.0)],
            "length": 100.0,
            "max_speed": 13.89,
            "lanes": 1,
            "edge_type": "highway.residential",
            "priority": 3,
        },
    ]
    app_state.set_map_data(nodes_data, edges_data)
    app_state.sources.associate("src_2", "-370320174#4")
    app_state.sources.associate("api_global_gius8", "-103342059#0")

    gm = GraphManager(app_state=app_state, embedding_dim=16)
    pipeline = IngestionPipeline(app_state=app_state)
    hub = IngestionHub(pipeline=pipeline)
    router = DataFlowRouter(app_state=app_state, graph_manager=gm)

    hub.register_listener(lambda sid, p, m: router.handle_data_flow(sid, p))

    # Route packet using external MQTT device alias 'loop_01'
    csv_payload = ["2026-10-19,00:03:34,loop_01,-23.512239,-51.235280,1,CAR,94,241"]
    accepted = hub.route_packet("loop_01", csv_payload)
    assert accepted is True
    assert "-370320174#4" in gm.direct_edge_metrics
    assert abs(gm.direct_edge_metrics["-370320174#4"]["speed"] - (94.0 / 3.6)) < 0.05
    assert gm.direct_edge_metrics["-370320174#4"]["density"] == pytest.approx(8.41, abs=0.2)

    # Verify EdgePayloadFormatter does not broadcast waze latest_value=1.0 across unobserved edges
    hist_payload = EdgePayloadFormatter.format_edge_payload(
        flat_data={"other_metric": 0.0},
        app_state=app_state,
    )
    assert hist_payload["-370320174#4"]["density"] < 20.0

