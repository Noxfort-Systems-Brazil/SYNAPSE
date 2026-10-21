# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
from unittest.mock import MagicMock

from src.domain.entities import DataSource, SourceStatus, SourceType, MapEdge, MapNode
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


def test_local_sensor_does_not_invoke_cartographer(mock_network_and_app_state):
    """
    Verifies that local sensors (is_local=True) never invoke CartographerAgent,
    even if they have GPS or coordinates in metadata.
    """
    app_state, edge_ida, _, projection_svc = mock_network_and_app_state
    reconciler = SpatialReconciler(app_state, projection_service=projection_svc)
    agent_factory = MagicMock()

    # Local sensor with predefined association
    local_source = DataSource(
        id="src_camera_local",
        name="Camera Av Brasil",
        source_type=SourceType.MQTT,
        is_local=True,
        metadata={"edge_id": "-370318891#2", "x": 500.0, "y": 700.0}
    )

    candidates = reconciler.find_candidate_edges(
        local_source,
        agent_factory=agent_factory,
        data_chunk=[{"count": 10}]
    )

    # Returned pre-associated edge directly without Cartographer
    assert len(candidates) >= 1
    assert candidates[0].id == "-370318891#2"
    agent_factory.get_or_create_cartographer.assert_not_called()
