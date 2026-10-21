# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
import numpy as np
from unittest.mock import MagicMock

from src.domain.entities import DataSource, SourceStatus, SourceType, MapEdge, MapNode
from src.services.linguist_service import LinguistService
from src.agents.compass_agent import CompassAgent
from src.services.geo_projection_service import GeoProjectionService, SumoLocationParams
from src.linguist.spatial_reconciler import SpatialReconciler


@pytest.fixture
def in_memory_projection_service():
    """
    Clean Architecture / DIP Fixture:
    Provides an in-memory GeoProjectionService without any disk I/O.
    """
    params = SumoLocationParams(
        net_offset=(-475481.54, 2600660.66),
        conv_boundary=(0.00, 0.00, 715.96, 930.36),
        orig_boundary=(-51.240163, -23.515986, -51.233151, -23.507576),
        proj_parameter="+proj=utm +zone=22 +ellps=WGS84 +datum=WGS84 +units=m +no_defs"
    )
    return GeoProjectionService(params=params)


@pytest.fixture
def mock_network_and_app_state(in_memory_projection_service):
    """
    Clean Architecture Fixture:
    Sets up domain entities and in-memory mock app_state.
    """
    app_state = MagicMock()
    app_state.sources = MagicMock()

    # SUMO coordinate edges: (500, 700) -> (550, 750)
    edge_ida = MapEdge(
        id="-370318891#2",
        from_node="junction_1",
        to_node="junction_2",
        shape=[(500.0, 700.0), (550.0, 750.0)]
    )
    edge_volta = MapEdge(
        id="370318891#2",
        from_node="junction_2",
        to_node="junction_1",
        shape=[(550.0, 750.0), (500.0, 700.0)]
    )
    node_1 = MapNode(id="junction_1", x=500.0, y=700.0, node_type="traffic_light")
    node_2 = MapNode(id="junction_2", x=550.0, y=750.0, node_type="junction")

    all_edges = [edge_ida, edge_volta]
    all_nodes = [node_1, node_2]

    app_state.get_all_edges.return_value = all_edges
    app_state.get_all_nodes.return_value = all_nodes
    app_state.get_edge.side_effect = lambda eid: next((e for e in all_edges if e.id == eid), None)
    app_state.get_element_for_source.return_value = None
    app_state.get_map_source_path.return_value = None

    return app_state, edge_ida, edge_volta, in_memory_projection_service


def test_tomtom_admission_with_cartographer_and_linguist_pass(mock_network_and_app_state):
    """
    Pure Dependency Inversion (DIP) Test:
    - Global sensor (TomTom, is_local=False) with 1 sample.
    - PhysicsValidator injected directly via constructor (no patch.object).
    - Cartographer is invoked, matches polyline to -370318891#2.
    - Compass reconciles orientation.
    - Sensor is associated to edge in AppState and promoted to ACTIVE.
    """
    app_state, edge_ida, edge_volta, projection_svc = mock_network_and_app_state
    ingestion = MagicMock()
    pipeline = MagicMock()
    ingestion.get_pipeline.return_value = pipeline
    agent_factory = MagicMock()

    source = DataSource(
        id="api_global_9r26o",
        name="Tomtom Flow",
        source_type=SourceType.API,
        is_local=False,
        status=SourceStatus.QUARANTINE,
        metadata={"extraction_path": ["flowSegmentData", "currentSpeed_kmh"]}
    )
    app_state.get_all_data_sources.return_value = [source]
    pipeline.has_enough_data.return_value = True

    tomtom_chunk = [
        {
            "flowSegmentData": {
                "currentSpeed_kmh": 45.0,
                "coordinates": {
                    "coordinate": [
                        {"latitude": -23.5097475, "longitude": -51.2351221},
                        {"latitude": -23.5098522, "longitude": -51.2352354}
                    ]
                }
            }
        }
    ]
    pipeline.get_quarantine_data.return_value = tomtom_chunk

    # 1. Mock LinguistAgent
    mock_linguist = MagicMock()
    mock_linguist.train_step.return_value = 0.01
    mock_linguist.inference.return_value = {"is_valid": True, "is_anomaly": False}
    agent_factory.get_or_create_linguist.return_value = mock_linguist

    # 2. Mock Cartographer matching
    mock_cartographer = MagicMock()
    mock_cartographer.match_polyline.return_value = {
        "edge_id": "-370318891#2",
        "confidence": 0.96,
        "method": "geometric",
        "entropy": 0.05
    }
    agent_factory.get_or_create_cartographer.return_value = mock_cartographer

    # 3. Mock CompassAgent (LSP spec)
    mock_compass = MagicMock(spec=CompassAgent)
    mock_compass.orient_and_reconcile.return_value = {
        "orientation": "IDA",
        "primary_edge_id": "-370318891#2",
        "secondary_edge_id": None,
        "confidence": 0.95,
        "vector": (1.0, 0.0),
        "method": "single_edge_fast"
    }
    agent_factory.get_or_create_compass.return_value = mock_compass
    agent_factory.get_or_create_specialist.return_value = MagicMock()

    # 4. DIP Injections (No patch.object!)
    mock_physics_validator = MagicMock()
    mock_physics_validator.validate.return_value = True

    mock_semantic_classifier = MagicMock()
    mock_semantic_classifier.classify.return_value = ("Vehicle Speed", "km/h", 0.98)

    mock_series_extractor = MagicMock()
    mock_series_extractor.extract.return_value = np.array([45.0])

    spatial_reconciler = SpatialReconciler(
        app_state=app_state,
        projection_service=projection_svc,
    )

    service = LinguistService(
        app_state=app_state,
        ingestion_worker=ingestion,
        agent_factory=agent_factory,
        series_extractor=mock_series_extractor,
        semantic_classifier=mock_semantic_classifier,
        physics_validator=mock_physics_validator,
        spatial_reconciler=spatial_reconciler,
    )

    # Execute workflow
    service.run_check()

    # Verifications:
    # A. Cartographer was called for global sensor with projected polyline
    agent_factory.get_or_create_cartographer.assert_called_once_with("api_global_9r26o", app_state=app_state)
    mock_cartographer.match_polyline.assert_called_once()
    agent_factory.release_cartographer.assert_called_once_with("api_global_9r26o")

    # B. Global sensor must NOT be statically bound to an edge in AppState
    app_state.sources.associate.assert_not_called()
    assert source.metadata["matched_edge_id"] == "-370318891#2"
    assert source.metadata["map_matching_method"] in ["geometric", "geometric_rtree"]

    # C. Promoted to ACTIVE
    assert source.status == SourceStatus.ACTIVE
    pipeline.promote_to_active.assert_called_once_with("api_global_9r26o")
