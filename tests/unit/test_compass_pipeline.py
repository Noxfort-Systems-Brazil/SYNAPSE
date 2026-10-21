# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest

from src.domain.entities import DataSource, SourceType, MapEdge
from src.pipeline.compass_pipeline import CompassPipeline


@pytest.fixture
def sample_edges():
    """Provides two opposing edges representing a two-way street."""
    # Edge A: West to East (shape: (0, 0) -> (100, 0)) -> Centro
    edge_a = MapEdge(
        id="edge_centro",
        from_node="node_west",
        to_node="node_centro",
        shape=[(0.0, 0.0), (100.0, 0.0)],
        real_name="Avenida Brasil Sentido Centro",
        weight=1.0,
        length=100.0,
        lanes=2,
    )
    # Edge B: East to West (shape: (100, 0) -> (0, 0)) -> Bairro
    edge_b = MapEdge(
        id="-edge_centro",
        from_node="node_centro",
        to_node="node_bairro",
        shape=[(100.0, 0.0), (0.0, 0.0)],
        real_name="Avenida Brasil Sentido Bairro",
        weight=1.0,
        length=100.0,
        lanes=2,
    )
    return [edge_a, edge_b]


def test_compass_pipeline_no_candidates():
    """Verifies that empty candidates list returns INDETERMINADO."""
    pipeline = CompassPipeline(confidence_threshold=0.6)
    source = DataSource(id="s1", name="Sensor 1", source_type=SourceType.API)

    result = pipeline.orient_and_reconcile(source, candidate_edges=[])
    assert result["orientation"] == "INDETERMINADO"
    assert result["primary_edge_id"] is None
    assert result["confidence"] == 0.0
    assert result["method"] == "no_candidates"


def test_compass_pipeline_fast_path_one_way(sample_edges):
    """Verifies O(1) fast-path when street is one-way (single candidate edge)."""
    pipeline = CompassPipeline(confidence_threshold=0.6)
    source = DataSource(id="s1", name="Camera Rua Direita", source_type=SourceType.API)

    result = pipeline.orient_and_reconcile(source, candidate_edges=[sample_edges[0]])
    assert result["orientation"] == "IDA"
    assert result["primary_edge_id"] == "edge_centro"
    assert result["confidence"] == 1.0
    assert result["method"] == "single_edge_fast"
    # Vector should be pointing East: (1.0, 0.0)
    assert pytest.approx(result["vector"][0], rel=1e-3) == 1.0
    assert pytest.approx(result["vector"][1], abs=1e-3) == 0.0


def test_compass_pipeline_two_way_disambiguation_keywords(sample_edges):
    """Verifies disambiguation between opposing directions using semantic keywords."""
    pipeline = CompassPipeline(confidence_threshold=0.6)

    # Sensor referencing "centro"
    src_centro = DataSource(
        id="s_c",
        name="Radar Av Brasil - Acesso Centro",
        source_type=SourceType.API,
    )
    res_c = pipeline.orient_and_reconcile(src_centro, candidate_edges=sample_edges)
    assert res_c["orientation"] == "IDA"
    assert res_c["primary_edge_id"] == "edge_centro"

    # Sensor referencing "bairro"
    src_bairro = DataSource(
        id="s_b",
        name="Radar Av Brasil - Retorno Bairro",
        source_type=SourceType.API,
    )
    res_b = pipeline.orient_and_reconcile(src_bairro, candidate_edges=sample_edges)
    assert res_b["orientation"] == "VOLTA"
    assert res_b["primary_edge_id"] == "-edge_centro"


def test_compass_pipeline_two_way_bearing(sample_edges):
    """Verifies that geometric bearing aligns sensor with the correct edge vector."""
    pipeline = CompassPipeline(confidence_threshold=0.6)

    # Angle 0 degrees = East (1.0, 0.0) -> edge_centro
    src_east = DataSource(
        id="s_east",
        name="Sensor Direcional",
        source_type=SourceType.API,
        metadata={"bearing": 0.0},
    )
    res_east = pipeline.orient_and_reconcile(src_east, candidate_edges=sample_edges)
    assert res_east["primary_edge_id"] == "edge_centro"

    # Angle 180 degrees = West (-1.0, 0.0) -> -edge_centro
    src_west = DataSource(
        id="s_west",
        name="Sensor Direcional",
        source_type=SourceType.API,
        metadata={"bearing": 180.0},
    )
    res_west = pipeline.orient_and_reconcile(src_west, candidate_edges=sample_edges)
    assert res_west["primary_edge_id"] == "-edge_centro"


def test_compass_pipeline_prior_metadata_orientation(sample_edges):
    """Verifies that pre-configured orientation in metadata directly influences disambiguation."""
    pipeline = CompassPipeline(confidence_threshold=0.6)

    # Sensor with generic name but explicit VOLTA orientation metadata
    src_volta = DataSource(
        id="s_meta_v",
        name="Camera",
        source_type=SourceType.API,
        metadata={"orientation": "VOLTA"},
    )
    res_v = pipeline.orient_and_reconcile(src_volta, candidate_edges=sample_edges)
    assert res_v["orientation"] == "VOLTA"
    assert res_v["primary_edge_id"] == "-edge_centro"
    assert res_v["confidence"] > 0.90


def test_compass_pipeline_option3_ambiguous_coin_flip_guard(sample_edges):
    """Option 3: Verifies that ambiguous two-way sensor blocks coin flip and returns INDETERMINADO."""
    pipeline = CompassPipeline(confidence_threshold=0.65, margin_threshold=0.15)

    # Generic sensor without directional keywords, bearing, or coordinates
    src_ambiguous = DataSource(
        id="s_ambiguous",
        name="Waze Sensor 99",
        connection_string="https://api.waze.com/traffic",
        source_type=SourceType.API,
    )
    # Neutral candidate edges without matching to_node in name
    neutral_edge_a = MapEdge(
        id="edge_1",
        from_node="j1",
        to_node="j2",
        shape=[(0.0, 0.0), (100.0, 0.0)],
        real_name="Avenida X",
        weight=1.0,
        length=100.0,
        lanes=2,
    )
    neutral_edge_b = MapEdge(
        id="-edge_1",
        from_node="j2",
        to_node="j1",
        shape=[(100.0, 0.0), (0.0, 0.0)],
        real_name="Avenida X",
        weight=1.0,
        length=100.0,
        lanes=2,
    )

    res = pipeline.orient_and_reconcile(src_ambiguous, candidate_edges=[neutral_edge_a, neutral_edge_b])

    # Coin-flip must be REFUSED:
    assert res["orientation"] == "INDETERMINADO"
    assert res["primary_edge_id"] is None
    assert res["method"] == "ambiguous_coin_flip_guard"
    assert res["margin"] < 0.15
