# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
from unittest.mock import MagicMock

from src.domain.entities import DataSource, SourceType, SourceStatus, MapEdge
from src.agents.compass_agent import CompassAgent, TelemetryMode


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


def test_compass_agent_inference_delegation(sample_edges):
    """Verifies that CompassAgent conforms to BaseAgent and delegates to pipeline."""
    mock_pipeline = MagicMock()
    mock_pipeline.orient_and_reconcile.return_value = {
        "orientation": "IDA",
        "primary_edge_id": "edge_centro",
        "confidence": 0.99,
        "method": "mock",
    }

    agent = CompassAgent(pipeline=mock_pipeline)
    source = DataSource(id="s1", name="Cam", source_type=SourceType.API)

    # Via unified BaseAgent inference
    out = agent.inference({"source": source, "candidate_edges": sample_edges})
    assert out["orientation"] == "IDA"
    assert out["primary_edge_id"] == "edge_centro"
    mock_pipeline.orient_and_reconcile.assert_called_once()


def test_compass_agent_logging_traceability(sample_edges, caplog):
    """Verifies that CompassAgent logs lifecycle, inputs, and results clearly."""
    mock_pipeline = MagicMock()
    mock_pipeline.orient_and_reconcile.return_value = {
        "orientation": "IDA",
        "primary_edge_id": "edge_centro",
        "confidence": 0.95,
        "method": "fast_path",
    }

    with caplog.at_level("INFO"):
        agent = CompassAgent(pipeline=mock_pipeline)
        source = DataSource(
            id="src_trace_01",
            name="Camera Norte",
            source_type=SourceType.API,
            status=SourceStatus.QUARANTINE,
            metadata={"orientation": "IDA"},
        )

        result = agent.orient_and_reconcile(
            source=source,
            candidate_edges=sample_edges,
            data_chunk=[{"val": 1}],
            semantic_type="Vehicle Count",
        )

        assert result["orientation"] == "IDA"
        # Check logs
        assert "Reconciliação direcional solicitada para sensor 'Camera Norte'" in caplog.text
        assert "src_trace_01" in caplog.text
        assert "Quarentena: 1" in caplog.text
        assert "Reconciliação concluída para 'Camera Norte'" in caplog.text
        assert "Aresta Primária='edge_centro'" in caplog.text


def test_compass_agent_telemetry_mode_classification(sample_edges):
    """Verifies that CompassAgent accurately tags the operational TelemetryMode."""
    agent = CompassAgent()

    # 1. One-way
    src1 = DataSource(id="s1", name="Cam")
    assert agent.classify_telemetry_mode(src1, [sample_edges[0]], None) == TelemetryMode.ONE_WAY

    # 2. Fluid Vector (Option 1)
    chunk_v = [{"direction_deg": 90.0}]
    assert agent.classify_telemetry_mode(src1, sample_edges, chunk_v) == TelemetryMode.FLUID_VECTOR

    # 3. Multichannel (Option 2)
    chunk_m = [{"inbound": 10, "outbound": 20}]
    assert agent.classify_telemetry_mode(src1, sample_edges, chunk_m) == TelemetryMode.MULTICHANNEL

    # 4. Scalar ambiguous (Option 3)
    chunk_s = [{"speed": 40.0}]
    assert agent.classify_telemetry_mode(src1, sample_edges, chunk_s) == TelemetryMode.SCALAR_AMBIGUOUS
