# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
import numpy as np
from unittest.mock import MagicMock

from src.domain.entities import DataSource, SourceStatus, SourceType, MapEdge, MapNode
from src.linguist.local_topology_matcher import LocalTopologyMatcher
from src.linguist.global_cartographer_matcher import GlobalCartographerMatcher
from src.linguist.compass_reconciler import CompassReconciler
from src.linguist.spatial_reconciler import SpatialReconciler
from src.services.geo_projection_service import GeoProjectionService, SumoLocationParams


@pytest.fixture
def mock_edges_and_app_state():
    app_state = MagicMock()
    app_state.sources = MagicMock()

    edge_ida = MapEdge(
        id="edge_1",
        from_node="node_A",
        to_node="node_B",
        shape=[(10.0, 10.0), (50.0, 10.0)]
    )
    edge_volta = MapEdge(
        id="-edge_1",
        from_node="node_B",
        to_node="node_A",
        shape=[(50.0, 10.0), (10.0, 10.0)]
    )
    all_edges = [edge_ida, edge_volta]

    app_state.get_all_edges.return_value = all_edges
    app_state.get_edge.side_effect = lambda eid: next((e for e in all_edges if e.id == eid), None)
    app_state.get_element_for_source.return_value = None

    return app_state, edge_ida, edge_volta


def test_local_topology_matcher_direct_metadata(mock_edges_and_app_state):
    """Verifies that LocalTopologyMatcher resolves edge from metadata and opposing edge."""
    app_state, edge_ida, edge_volta = mock_edges_and_app_state
    matcher = LocalTopologyMatcher(app_state)

    source = DataSource(
        id="src_local_loop",
        name="Laço Indutivo",
        is_local=True,
        metadata={"edge_id": "edge_1"}
    )
    candidates = matcher.find_candidates(source)
    assert len(candidates) == 2
    assert candidates[0].id == "edge_1"
    assert candidates[1].id == "-edge_1"


def test_local_topology_matcher_proximity_fallback(mock_edges_and_app_state):
    """Verifies that LocalTopologyMatcher uses geometric proximity when edge_id is missing."""
    app_state, edge_ida, edge_volta = mock_edges_and_app_state
    matcher = LocalTopologyMatcher(app_state)

    source = DataSource(
        id="src_local_radar",
        name="Radar Fixo Local",
        is_local=True,
        metadata={"x": 12.0, "y": 10.5}  # Very close to edge_1
    )
    candidates = matcher.find_candidates(source)
    assert len(candidates) >= 1
    assert candidates[0].id == "edge_1"


def test_global_cartographer_matcher_executes_and_releases(mock_edges_and_app_state):
    """Verifies that GlobalCartographerMatcher invokes Cartographer and releases it."""
    app_state, edge_ida, _ = mock_edges_and_app_state

    # Projection in-memory
    params = SumoLocationParams(
        net_offset=(0.0, 0.0),
        conv_boundary=(0.0, 0.0, 100.0, 100.0),
        orig_boundary=(-50.0, -20.0, -49.0, -19.0)
    )
    proj_svc = GeoProjectionService(params=params)

    matcher = GlobalCartographerMatcher(app_state, projection_service=proj_svc)

    source = DataSource(
        id="api_global_test",
        name="Global Feed",
        is_local=False,
        metadata={"polyline": [(-49.5, -19.5), (-49.4, -19.4)]}
    )

    mock_cartographer = MagicMock()
    mock_cartographer.match_polyline.return_value = {
        "edge_id": "edge_1",
        "confidence": 0.95,
        "method": "neural",
        "entropy": 0.02
    }
    agent_factory = MagicMock()
    agent_factory.get_or_create_cartographer.return_value = mock_cartographer

    candidates = matcher.match(source, agent_factory=agent_factory)

    assert len(candidates) >= 1
    assert candidates[0].id == "edge_1"
    agent_factory.get_or_create_cartographer.assert_called_once_with("api_global_test", app_state=app_state)
    agent_factory.release_cartographer.assert_called_once_with("api_global_test")
    assert source.metadata["matched_edge_id"] == "edge_1"


def test_global_cartographer_matcher_pure_deterministic(mock_edges_and_app_state):
    """Verifies that GlobalCartographerMatcher matches directly via FastMapMatcher without any agent_factory."""
    app_state, edge_ida, edge_volta = mock_edges_and_app_state

    # In-memory projection (identity scale for testing)
    params = SumoLocationParams(
        net_offset=(0.0, 0.0),
        conv_boundary=(0.0, 0.0, 100.0, 100.0),
        orig_boundary=(0.0, 0.0, 100.0, 100.0)
    )
    proj_svc = GeoProjectionService(params=params)

    matcher = GlobalCartographerMatcher(app_state, projection_service=proj_svc)

    # Source with points near edge_1: [(0,0), (100,0)]
    source = DataSource(
        id="waze_pure_geo",
        name="Waze Jam 23 de Maio",
        is_local=False,
        metadata={"polyline": [(10.0, 1.0), (50.0, 2.0), (90.0, 1.0)]}
    )

    candidates = matcher.match(source, agent_factory=None)

    assert len(candidates) >= 1
    assert candidates[0].id == "edge_1"
    assert source.metadata["matched_edge_id"] == "edge_1"
    assert source.metadata["map_matching_method"] == "geometric_rtree"


def test_compass_reconciler_associates_and_releases(mock_edges_and_app_state):
    """Verifies that CompassReconciler invokes CompassAgent and associates edge in AppState."""
    app_state, edge_ida, edge_volta = mock_edges_and_app_state
    reconciler = CompassReconciler(app_state)

    source = DataSource(
        id="src_radar_orient",
        name="Radar Orientação",
        is_local=True,
        metadata={}
    )
    mock_compass = MagicMock()
    mock_compass.orient_and_reconcile.return_value = {
        "orientation": "IDA",
        "primary_edge_id": "edge_1",
        "secondary_edge_id": None,
        "vector": (1.0, 0.0),
    }
    agent_factory = MagicMock()
    agent_factory.get_or_create_compass.return_value = mock_compass

    data_chunk = [{"val": 10}]
    data_np = np.array([10.0])

    res = reconciler.reconcile(
        source=source,
        candidate_edges=[edge_ida, edge_volta],
        agent_factory=agent_factory,
        data_chunk=data_chunk,
        data_np=data_np,
        sem_type="Traffic Flow"
    )

    assert res["primary_edge_id"] == "edge_1"
    app_state.sources.associate.assert_called_with("src_radar_orient", "edge_1")
    agent_factory.release_compass.assert_called_once_with("src_radar_orient")
    assert source.metadata["orientation"] == "IDA"


def test_spatial_reconciler_pure_orchestrator(mock_edges_and_app_state):
    """Verifies that SpatialReconciler delegates cleanly to the specialized sub-components."""
    app_state, edge_ida, _ = mock_edges_and_app_state

    mock_local = MagicMock()
    mock_local.find_candidates.return_value = [edge_ida]

    mock_global = MagicMock()
    mock_global.match.return_value = [edge_ida]

    mock_compass = MagicMock()
    mock_compass.reconcile.return_value = {"primary_edge_id": "edge_1"}

    orchestrator = SpatialReconciler(
        app_state=app_state,
        local_matcher=mock_local,
        global_matcher=mock_global,
        compass_reconciler=mock_compass,
    )

    # 1. Local sensor routes to local_matcher
    local_source = DataSource(id="s_local", name="Local", is_local=True)
    res_local = orchestrator.find_candidate_edges(local_source)
    mock_local.find_candidates.assert_called_once_with(local_source)
    mock_global.match.assert_not_called()
    assert res_local == [edge_ida]

    # 2. Global sensor routes to global_matcher
    global_source = DataSource(id="s_global", name="Global", is_local=False)
    agent_factory = MagicMock()
    res_global = orchestrator.find_candidate_edges(global_source, agent_factory=agent_factory, data_chunk=[])
    mock_global.match.assert_called_once_with(source=global_source, agent_factory=agent_factory, data_chunk=[])
    assert res_global == [edge_ida]

    # 3. Reconcile orientation routes to compass_reconciler
    orchestrator.reconcile_orientation(
        source=local_source,
        candidate_edges=[edge_ida],
        agent_factory=agent_factory,
        data_chunk=None,
        data_np=np.array([1.0]),
        sem_type="Flow"
    )
    mock_compass.reconcile.assert_called_once()
