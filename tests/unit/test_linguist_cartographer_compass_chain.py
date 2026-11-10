# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from src.domain.entities import DataSource, SourceStatus, SourceType, MapEdge, MapNode
from src.services.linguist_service import LinguistService
from src.agents.compass_agent import CompassAgent


@pytest.fixture
def mock_network_and_app_state():
    app_state = MagicMock()
    app_state.sources = MagicMock()

    edge_ida = MapEdge(
        id="edge_100",
        from_node="node_A",
        to_node="node_B",
        shape=[(0.0, 0.0), (100.0, 0.0)]
    )
    edge_volta = MapEdge(
        id="-edge_100",
        from_node="node_B",
        to_node="node_A",
        shape=[(100.0, 0.0), (0.0, 0.0)]
    )
    node_a = MapNode(id="node_A", x=0.0, y=0.0, node_type="junction")
    node_b = MapNode(id="node_B", x=100.0, y=0.0, node_type="junction")

    all_edges = [edge_ida, edge_volta]
    all_nodes = [node_a, node_b]

    app_state.get_all_edges.return_value = all_edges
    app_state.get_all_nodes.return_value = all_nodes
    app_state.get_edge.side_effect = lambda eid: next((e for e in all_edges if e.id == eid), None)
    app_state.get_element_for_source.return_value = None

    return app_state, edge_ida, edge_volta


def test_full_admission_chain_linguist_cartographer_compass(mock_network_and_app_state):
    """
    Verifies that during sensor onboarding with GPS coordinates:
    1. LinguistAgent validates data grammar and physics.
    2. CartographerAgent matches point (x, y) to edge_100 and discovers opposing edge.
    3. CompassAgent reconciles directional orientation (IDA vs VOLTA).
    4. Both Cartographer and Compass are cleanly released (ephemeral lifecycle).
    5. Sensor is promoted to ACTIVE and assigned to Specialist.
    """
    app_state, edge_ida, edge_volta = mock_network_and_app_state
    ingestion = MagicMock()
    pipeline = MagicMock()
    ingestion.get_pipeline.return_value = pipeline
    agent_factory = MagicMock()

    source = DataSource(
        id="src_radar_geo",
        name="Radar Av Brasil GPS",
        source_type=SourceType.API,
        is_local=False,
        status=SourceStatus.QUARANTINE,
        metadata={"x": 50.0, "y": 1.0}  # Coordinates near edge_100
    )
    app_state.get_all_data_sources.return_value = [source]

    pipeline.has_enough_data.return_value = True
    pipeline.get_quarantine_data.return_value = [
        {"speed": 60.0, "timestamp": 1000},
        {"speed": 62.0, "timestamp": 1001},
        {"speed": 58.0, "timestamp": 1002},
        {"speed": 61.0, "timestamp": 1003},
        {"speed": 59.0, "timestamp": 1004}
    ]

    # 1. Mock LinguistAgent
    mock_linguist = MagicMock()
    mock_linguist.train_step.return_value = 0.005  # Passed grammar
    mock_linguist.inference.return_value = {"is_valid": True, "is_anomaly": False, "physics_residual": 0.01}
    agent_factory.get_or_create_linguist.return_value = mock_linguist

    # 2. Mock Cartographer matching
    mock_cartographer = MagicMock()
    mock_cartographer.match_point.return_value = {
        "edge_id": "edge_100",
        "confidence": 0.99,
        "method": "heuristic",
        "entropy": 0.1
    }
    agent_factory.get_or_create_cartographer.return_value = mock_cartographer

    # 3. Mock CompassAgent
    mock_compass = MagicMock(spec=CompassAgent)
    mock_compass.orient_and_reconcile.return_value = {
        "orientation": "IDA",
        "primary_edge_id": "edge_100",
        "secondary_edge_id": None,
        "channels": {},
        "confidence": 0.95,
        "vector": (1.0, 0.0),
        "method": "semantic_neural_reconciliation"
    }
    agent_factory.get_or_create_compass.return_value = mock_compass

    # 4. Mock SpecialistAgent
    mock_specialist = MagicMock()
    agent_factory.get_or_create_specialist.return_value = mock_specialist

    service = LinguistService(app_state, ingestion, agent_factory)

    with patch.object(service.physics_validator, "validate", return_value=True), \
         patch.object(service.semantic_classifier, "classify", return_value=("Vehicle Speed", "km/h", 0.98)), \
         patch.object(service.series_extractor, "extract", return_value=np.array([60.0, 62.0, 58.0, 61.0, 59.0])):

        service.run_check()

    # --- Verifications ---

    # A. Cartographer was invoked and released
    agent_factory.get_or_create_cartographer.assert_called_once_with("src_radar_geo", app_state=app_state)
    mock_cartographer.match_point.assert_called_once_with(50.0, 1.0)
    agent_factory.release_cartographer.assert_called_once_with("src_radar_geo")

    # B. Compass was invoked with discovered candidates and released
    agent_factory.get_or_create_compass.assert_called_once_with("src_radar_geo")
    mock_compass.orient_and_reconcile.assert_called_once()
    assert mock_compass.orient_and_reconcile.call_args[1]["candidate_edges"][0].id == "edge_100"
    agent_factory.release_compass.assert_called_once_with("src_radar_geo")

    # C. Association and metadata enrichment
    app_state.sources.associate.assert_not_called()
    assert source.metadata["orientation"] == "IDA"
    assert source.metadata["orientation_vector"] == (1.0, 0.0)

    # D. Promoted to ACTIVE
    assert source.status == SourceStatus.ACTIVE
    pipeline.promote_to_active.assert_called_once_with("src_radar_geo")
