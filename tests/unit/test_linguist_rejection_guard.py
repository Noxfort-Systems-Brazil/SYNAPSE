# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
import numpy as np
from unittest.mock import MagicMock

from src.domain.entities import DataSource, SourceStatus, SourceType, MapEdge, MapNode
from src.services.linguist_service import LinguistService
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


def test_linguist_physics_rejection_blocks_cartographer_and_association(mock_network_and_app_state):
    """
    CRITICAL REALISM GUARD TEST (Pure DIP):
    If Linguist physical validation fails:
    - Cartographer is NEVER invoked.
    - No edge association is sent or stored.
    - Source is NOT promoted to ACTIVE.
    """
    app_state, _, _, projection_svc = mock_network_and_app_state
    ingestion = MagicMock()
    pipeline = MagicMock()
    ingestion.get_pipeline.return_value = pipeline
    agent_factory = MagicMock()

    source = DataSource(
        id="api_global_waze_fake",
        name="Waze Teleporting",
        source_type=SourceType.API,
        is_local=False,
        status=SourceStatus.QUARANTINE,
    )
    app_state.get_all_data_sources.return_value = [source]
    pipeline.has_enough_data.return_value = True

    waze_chunk = [
        {
            "jams": [
                {
                    "line": [
                        {"x": -51.236102, "y": -23.512398},
                        {"x": -51.236315, "y": -23.512521}
                    ]
                }
            ]
        }
    ]
    pipeline.get_quarantine_data.return_value = waze_chunk

    mock_linguist = MagicMock()
    mock_linguist.train_step.return_value = 0.02
    agent_factory.get_or_create_linguist.return_value = mock_linguist

    # DIP Injections (Physics fails!)
    mock_physics_validator = MagicMock()
    mock_physics_validator.validate.return_value = False

    mock_semantic_classifier = MagicMock()
    mock_semantic_classifier.classify.return_value = ("Traffic Flow", "veh/h", 0.90)

    mock_series_extractor = MagicMock()
    mock_series_extractor.extract.return_value = np.array([2000.0])

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

    # Execute check
    service.run_check()

    # Verifications:
    # 1. Cartographer was NEVER created or invoked
    agent_factory.get_or_create_cartographer.assert_not_called()

    # 2. No edge was associated
    app_state.sources.associate.assert_not_called()

    # 3. Source was NOT promoted
    assert source.status != SourceStatus.ACTIVE
    pipeline.promote_to_active.assert_not_called()


def test_global_sensor_without_candidate_edges_is_rejected(mock_network_and_app_state):
    """
    Verifies that if a global sensor has valid physics and grammar, but
    has NO candidate edges to bind (empty polyline / map matching fails),
    it is IMMEDIATELY REJECTED (SourceStatus.REJECTED), removed from pipeline buffers,
    and NOT promoted to ACTIVE.
    """
    app_state, _, _, projection_svc = mock_network_and_app_state
    ingestion = MagicMock()
    pipeline = MagicMock()
    ingestion.get_pipeline.return_value = pipeline
    agent_factory = MagicMock()

    source = DataSource(
        id="api_global_no_edges",
        name="Waze Without Geodata",
        source_type=SourceType.API,
        is_local=False,
        status=SourceStatus.QUARANTINE,
    )
    app_state.get_all_data_sources.return_value = [source]
    pipeline.has_enough_data.return_value = True

    # Empty jams feed (no coordinates)
    waze_empty_chunk = [{"jams": [], "startTime": "2026-10-17 12:00:00"}]
    pipeline.get_quarantine_data.return_value = waze_empty_chunk

    mock_linguist = MagicMock()
    mock_linguist.train_step.return_value = 0.01  # Passes grammar
    agent_factory.get_or_create_linguist.return_value = mock_linguist

    mock_physics_validator = MagicMock()
    mock_physics_validator.validate.return_value = True  # Passes physics

    mock_semantic_classifier = MagicMock()
    mock_semantic_classifier.classify.return_value = ("Vehicle Speed", "km/h", 0.95)

    mock_series_extractor = MagicMock()
    mock_series_extractor.extract.return_value = np.array([40.0])

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

    # Run check
    service.run_check()

    # Verifications:
    # 1. Source MUST be marked as REJECTED
    assert source.status == SourceStatus.REJECTED

    # 2. Pipeline MUST NOT promote to active
    pipeline.promote_to_active.assert_not_called()

    # 3. Pipeline MUST clean up buffer context
    pipeline.remove_source_context.assert_called_once_with("api_global_no_edges")

    # 4. No edge association occurred in AppState
    app_state.sources.associate.assert_not_called()
