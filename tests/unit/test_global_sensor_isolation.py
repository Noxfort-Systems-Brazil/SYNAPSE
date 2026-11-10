# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
from unittest.mock import MagicMock
from src.domain.entities import DataSource, SourceStatus, SourceType, MapEdge
from src.domain.source_repository import SourceRepository
from src.handlers.source.source_dto_mapper import SourceDtoMapper
from src.linguist.compass_reconciler import CompassReconciler
from src.agents.compass_agent import CompassAgent


def test_source_repository_blocks_global_associations():
    """Verifies that SourceRepository strictly prevents associating global sources to map elements."""
    repo = SourceRepository(storage=None)

    # 1. Local sensor can be associated
    local_src = DataSource(id="src_local_1", name="Camera Local", is_local=True)
    repo.add(local_src)
    repo.associate("src_local_1", "edge_100")
    assert repo.get_element_for_source("src_local_1") == "edge_100"
    assert repo.get_elements_for_source("src_local_1") == ["edge_100"]

    # 2. Global sensor CANNOT be statically associated
    global_src = DataSource(id="api_global_waze", name="Waze Feed", is_local=False)
    repo.add(global_src)
    repo.associate("api_global_waze", "edge_100")
    assert repo.get_element_for_source("api_global_waze") is None
    assert repo.get_elements_for_source("api_global_waze") == []
    assert repo.get_associations("edge_100") == ["src_local_1"]


def test_toggle_origin_cleans_associations():
    """Verifies that toggling a local sensor to global strips its static map associations."""
    repo = SourceRepository(storage=None)
    src = DataSource(id="src_toggle", name="Sensor Toggle", is_local=True)
    repo.add(src)
    repo.associate("src_toggle", "edge_200")
    assert repo.get_element_for_source("src_toggle") == "edge_200"

    # Toggle to Global -> association MUST be purged
    new_scope = repo.toggle_origin("src_toggle")
    assert new_scope is False
    assert repo.get_element_for_source("src_toggle") is None
    assert repo.get_associations("edge_200") == []


def test_source_dto_mapper_omits_association_for_global_sensors():
    """Verifies that SourceDtoMapper exposes None for associated_element if sensor is global."""
    app_state = MagicMock()
    app_state.get_element_for_source.return_value = "edge_999"

    global_src = DataSource(id="api_global_test", name="Global API", is_local=False)
    dto = SourceDtoMapper.to_summary_dto(global_src, app_state)

    assert dto["is_local"] is False
    assert dto["associated_element"] is None
    assert dto["associated_element_name"] is None
    assert dto["connection_string"] == ""

    local_src = DataSource(
        id="src_local_1",
        name="Camera 01",
        is_local=True,
        connection_string="https://prefeitura-traffic.duckdns.org/src_local_1",
    )
    local_dto = SourceDtoMapper.to_summary_dto(local_src, app_state)
    assert local_dto["connection_string"] == "https://prefeitura-traffic.duckdns.org/src_local_1"


def test_compass_reconciler_does_not_associate_global_sources():
    """Verifies that CompassReconciler enriches orientation metadata but does NOT call associate for global feeds."""
    app_state = MagicMock()
    app_state.sources = MagicMock()

    candidate_edge = MapEdge(
        id="edge_500",
        from_node="n1",
        to_node="n2",
        shape=[(0.0, 0.0), (100.0, 0.0)]
    )

    reconciler = CompassReconciler(app_state=app_state)
    agent_factory = MagicMock()
    mock_compass = MagicMock(spec=CompassAgent)
    mock_compass.orient_and_reconcile.return_value = {
        "orientation": "IDA",
        "primary_edge_id": "edge_500",
        "secondary_edge_id": None,
        "vector": (1.0, 0.0),
    }
    agent_factory.get_or_create_compass.return_value = mock_compass

    global_source = DataSource(
        id="api_global_waze_01",
        name="Waze Global",
        is_local=False,
        status=SourceStatus.QUARANTINE,
        metadata={"matched_edge_id": "edge_500"}
    )

    result = reconciler.reconcile(
        source=global_source,
        candidate_edges=[candidate_edge],
        agent_factory=agent_factory,
        data_chunk=[{"speed": 50}],
        data_np=None,
        sem_type="Traffic Flow"
    )

    # Compass oriented successfully
    assert result["orientation"] == "IDA"
    assert global_source.metadata["orientation"] == "IDA"
    assert global_source.metadata["orientation_vector"] == (1.0, 0.0)

    # Static association in AppState MUST NOT be called for global sensor
    app_state.sources.associate.assert_not_called()
