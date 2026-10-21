# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest

from src.domain.entities import DataSource, SourceType, MapEdge
from src.pipeline.compass_pipeline import CompassPipeline


@pytest.fixture
def sample_edges():
    """Provides two opposing edges representing a two-way street."""
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


def test_compass_pipeline_multichannel_metadata(sample_edges):
    """Verifies that multichannel sensor with metadata channels is split across opposing edges."""
    pipeline = CompassPipeline(confidence_threshold=0.6)
    source = DataSource(
        id="s_radar",
        name="Radar Portal Bidirecional",
        source_type=SourceType.API,
        metadata={"channels": {"pista_ida": "cam1", "pista_volta": "cam2"}},
    )

    result = pipeline.orient_and_reconcile(source, candidate_edges=sample_edges)
    assert result["orientation"] == "DUPLO"
    assert result["primary_edge_id"] == "edge_centro"
    assert result["secondary_edge_id"] == "-edge_centro"
    assert "pista_ida" in result["channels"]
    assert "pista_volta" in result["channels"]
    assert result["method"] == "multichannel_metadata_split"


def test_compass_pipeline_multichannel_payload(sample_edges):
    """Verifies that sensor payload with dual keys (inbound/outbound) triggers DUPLO orientation."""
    pipeline = CompassPipeline(confidence_threshold=0.6)
    source = DataSource(id="s_gantry", name="Pórtico Rodoviário", source_type=SourceType.API)
    data_chunk = [
        {"inbound": 45, "outbound": 38, "timestamp": 1700000000},
        {"inbound": 42, "outbound": 40, "timestamp": 1700000001},
    ]

    result = pipeline.orient_and_reconcile(source, candidate_edges=sample_edges, data_chunk=data_chunk)
    assert result["orientation"] == "DUPLO"
    assert result["primary_edge_id"] == "edge_centro"
    assert result["secondary_edge_id"] == "-edge_centro"
    assert result["channels"]["inbound"] == "edge_centro"
    assert result["channels"]["outbound"] == "-edge_centro"
    assert result["method"] == "multichannel_payload_split"


def test_compass_pipeline_option2_svision_multichannel(sample_edges):
    """Option 2: Verifies SVision multichannel bidirectional lanes."""
    pipeline = CompassPipeline(confidence_threshold=0.6)
    src_svision = DataSource(id="svision_dual", name="SVision Pórtico Central", source_type=SourceType.API)

    svision_chunk = [{
        "channels": [
            {"channel_id": "ch_east", "direction_deg": 0.0, "speed": 48.0, "density": 0.20},
            {"channel_id": "ch_west", "direction_deg": 180.0, "speed": 12.0, "density": 0.85},
        ]
    }]

    res = pipeline.orient_and_reconcile(src_svision, candidate_edges=sample_edges, data_chunk=svision_chunk)
    assert res["orientation"] == "DUPLO"
    assert res["primary_edge_id"] == "edge_centro"
    assert res["secondary_edge_id"] == "-edge_centro"
    assert res["method"] == "svision_multichannel_split"
    assert res["channels"]["ch_east"] == "edge_centro"
    assert res["channels"]["ch_west"] == "-edge_centro"


def test_compass_pipeline_option1_svision_fluid_vector(sample_edges):
    """Option 1: Verifies SVision fluid telemetry with direction_deg resolves direction deterministically."""
    pipeline = CompassPipeline(confidence_threshold=0.6)

    # 1. SVision pointing East (0 degrees) -> edge_centro
    src_east = DataSource(id="svision_east", name="SVision Paulista Leste", source_type=SourceType.API)
    svision_chunk_east = [{"speed": 45.0, "density": 0.25, "direction_deg": 0.0}]
    res_east = pipeline.orient_and_reconcile(src_east, candidate_edges=sample_edges, data_chunk=svision_chunk_east)
    assert res_east["orientation"] == "IDA"
    assert res_east["primary_edge_id"] == "edge_centro"
    assert res_east["method"] == "fluid_vector_alignment"
    assert res_east["confidence"] >= 0.85

    # 2. SVision pointing West (180 degrees) -> -edge_centro
    src_west = DataSource(id="svision_west", name="SVision Paulista Oeste", source_type=SourceType.API)
    svision_chunk_west = [{"speed": 14.0, "density": 0.82, "direction_deg": 180.0}]
    res_west = pipeline.orient_and_reconcile(src_west, candidate_edges=sample_edges, data_chunk=svision_chunk_west)
    assert res_west["orientation"] == "VOLTA"
    assert res_west["primary_edge_id"] == "-edge_centro"
    assert res_west["method"] == "fluid_vector_alignment"
    assert res_west["confidence"] >= 0.85


def test_compass_pipeline_option1_yolo_tracking_detections(sample_edges):
    """Option 1: Verifies Format A camera with YOLO tracking detection vectors."""
    pipeline = CompassPipeline(confidence_threshold=0.6)
    src_cam = DataSource(id="cam_yolo", name="Camera IA", source_type=SourceType.API)

    # Vehicle trackings moving West (-1.0, 0.0)
    data_chunk = [{
        "detections": [
            {"track_id": 1, "vector": [-2.0, 0.0]},
            {"track_id": 2, "vector": [-1.5, 0.0]},
        ]
    }]

    res = pipeline.orient_and_reconcile(src_cam, candidate_edges=sample_edges, data_chunk=data_chunk)
    assert res["orientation"] == "VOLTA"
    assert res["primary_edge_id"] == "-edge_centro"
    assert res["method"] == "fluid_vector_alignment"
