# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import json
import threading
import time
from collections import deque
from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pytest
import torch
import torch.nn as nn

from src.domain.entities import MapEdge, MapNode
from src.engine.cycle_processor import CycleProcessor
from src.engine.snapshot_builder import SnapshotBuilder
from src.ipc.ipc_protocol import IpcEvent, IpcResponse
from src.ipc.serializers import TelemetrySerializer, TopologySerializer
from src.kse.packet_builder import PacketBuilder
from src.managers.graph.node_factory import TrafficNodeFactory
from src.memory.temporal_memory import TemporalMemory
from src.models.modernbert import ModernBertEmbeddingModel
from src.pipeline.auditor_pipeline import AuditorPipeline
from src.slm.llm_worker_instance import LLMWorkerInstance
from src.utils.debug_logger import JsonLinesLogger


def test_lazy_node_allocation_and_fast_idle_tick_isolation():
    """Uninstrumented intersections skip eager GPU SpecialistAgent allocation and fast-path tick() in O(1)."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    hm_stub = SimpleNamespace(
        fallback_engine=SimpleNamespace(sensor_profiles={}),
        loader=SimpleNamespace(sensor_ids=[]),
    )

    nodes = [
        TrafficNodeFactory.create_traffic_node(
            MapNode(id=f"J_{i}", x=float(i), y=0.0, node_type="priority"),
            device=device,
            historical_manager=hm_stub,
            graph_manager=None,
        )
        for i in range(150)
    ]

    # Zero eager SpecialistAgent instantiations on uninstrumented map junctions
    assert all(n._agent is None for n in nodes)

    t0 = time.perf_counter()
    for n in nodes:
        n.tick()
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    assert elapsed_ms < 25.0
    assert all(n._agent is None and n.fallback_steps == 0 for n in nodes)

    # Active sensors lazily materialize strictly isolated SpecialistAgents
    nodes[0].step(18.5)
    nodes[1].step(42.0)
    assert nodes[0]._agent is not None and nodes[1]._agent is not None
    assert nodes[0].agent is not nodes[1].agent
    assert nodes[0].agent.tcn is not nodes[1].agent.tcn

    # Reset cycle flag and verify active sensor DOES run ghost_step() on dropout tick()
    nodes[0].state.reset_cycle()
    nodes[0].tick()
    assert nodes[0].fallback_steps == 1


def test_slim_ipc_serialization_and_topology_cache():
    """TelemetrySerializer strips 32-dim embeddings for IPC without mutating internal KSE snapshots."""
    emb = np.arange(32, dtype=np.float32)
    raw_results = {
        "processing_time": 0.012,
        "sensor_snapshot": {
            "N_1": {"embedding": emb, "value": 24.5, "status": "Active", "type": "real"},
            "edge_direct": {"density": 12.0, "speed": 14.0},
        },
    }

    slim = TelemetrySerializer.slim_global_results(raw_results)
    assert "embedding" not in slim["sensor_snapshot"]["N_1"]
    assert slim["sensor_snapshot"]["N_1"]["value"] == 24.5
    assert "embedding" in raw_results["sensor_snapshot"]["N_1"]  # Internal dict preserved!

    wire_json = IpcEvent(event="global_results", data=slim).to_json()
    parsed = json.loads(wire_json)
    assert parsed["event"] == "global_results"
    assert "embedding" not in parsed["data"]["sensor_snapshot"]["N_1"]

    resp_json = IpcResponse(id="r1", success=True, result={"v": np.float32(3.5)}).to_json()
    assert json.loads(resp_json)["result"]["v"] == pytest.approx(3.5)

    TopologySerializer.invalidate_cache()
    app_state = MagicMock()
    app_state.get_all_nodes.return_value = [MapNode(id="N1", x=1.0, y=2.0, node_type="priority")]
    app_state.get_all_edges.return_value = [
        MapEdge(id="E1", from_node="N1", to_node="N1", shape=[[0.0, 0.0], [1.0, 1.0]])
    ]
    topo_1 = TopologySerializer.serialize_topology(app_state)
    topo_2 = TopologySerializer.serialize_topology(app_state)
    assert topo_1 is topo_2
    TopologySerializer.invalidate_cache()
    topo_3 = TopologySerializer.serialize_topology(app_state)
    assert topo_3 is not topo_1 and topo_3 == topo_1


def test_rotating_async_jsonl_logger_and_lean_packet_builder(tmp_path, monkeypatch):
    """JsonLinesLogger enforces max_bytes rotation asynchronously and PacketBuilder caches TLS lookups."""
    monkeypatch.setattr("src.utils.debug_logger.get_log_dir", lambda: tmp_path)

    jlog = JsonLinesLogger(
        "rot_test", "pkt", max_bytes=180, backup_count=2, async_mode=True, max_queue_size=64
    )
    for idx in range(12):
        jlog.log({"seq": idx, "payload": "x" * 60})
    jlog.flush()
    jlog.close()

    base = jlog.file_path
    assert base is not None and base.exists()
    assert base.with_name(f"{base.name}.1").exists()
    assert base.with_name(f"{base.name}.2").exists()
    assert not base.with_name(f"{base.name}.3").exists()

    captured_inputs = []
    monkeypatch.setattr(
        "src.kse.packet_builder.carina_input_logger.log", lambda d: captured_inputs.append(d)
    )
    monkeypatch.setattr("src.kse.packet_builder.carina_output_logger.log", lambda d: None)

    mock_app = MagicMock()
    mock_app.get_all_edges.return_value = [
        SimpleNamespace(id="e1", length=100.0, lanes=2, signal_group_id=-1, to_node="J_TLS", max_speed=15.0, from_node="J_0"),
        SimpleNamespace(id="e2", length=120.0, lanes=2, signal_group_id=-1, to_node="J_TLS", max_speed=15.0, from_node="J_1"),
    ]
    mock_app.get_node.return_value = SimpleNamespace(tl_logic_id="tls_main", node_type="traffic_light")

    pkt = PacketBuilder.build(
        {"J_0": {"value": 15.0, "embedding": np.ones(32, dtype=np.float32)}},
        source="realtime",
        app_state=mock_app,
    )
    assert pkt is not None and len(pkt["traffic"]) == 2
    assert mock_app.get_node.call_count == 1  # Cached across incoming edges of J_TLS!
    assert "embedding" not in captured_inputs[0]["data"]["J_0"]


def test_auditor_single_sync_equivalence_and_modernbert_lock():
    """AuditorPipeline 2-phase async execution matches synchronous audit and ModernBERT slicing is thread-safe."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    pipe_a = AuditorPipeline(input_len=60, J=2, latent_dim=8, device=device)
    pipe_b = AuditorPipeline(
        model=pipe_a.model,
        calibrator=pipe_a.calibrator,
        physics_engine=pipe_a.physics_engine,
        input_len=60,
        device=device,
    )

    sig = torch.sin(torch.linspace(0, 6.28, 60, device=device)).unsqueeze(0)
    rep_sync = pipe_a.audit({"signature": sig})
    async_pack = pipe_b.audit_async({"signature": sig})
    assert "metrics_gpu" in async_pack and isinstance(async_pack["metrics_gpu"], torch.Tensor)
    rep_two_phase = pipe_b.finalize_audit(async_pack)

    assert rep_sync["score"] == pytest.approx(rep_two_phase["score"], rel=1e-5, abs=1e-6)
    assert rep_sync["physics_details"] == pytest.approx(rep_two_phase["physics_details"], rel=1e-5, abs=1e-6)

    # Verify GPU-native _build_temporal_signature matches masked and unmasked means
    x_temp = torch.tensor([[2.0, 10.0, 20.0], [4.0, 30.0, 40.0]], device=device)
    mask = torch.tensor([1.0, 0.0, 1.0], device=device)
    sig_masked = CycleProcessor._build_temporal_signature(x_temp, mask)
    assert torch.allclose(sig_masked, torch.tensor([[11.0, 22.0]], device=device))
    sig_zero_mask = CycleProcessor._build_temporal_signature(x_temp, torch.zeros(3, device=device))
    assert torch.allclose(sig_zero_mask, x_temp.mean(dim=1, keepdim=True).T)

    # Verify ModernBertEmbeddingModel default_num_layers is None and RLock protects concurrent slicing
    class _DummyTransformer(nn.Module):
        def __init__(self):
            super().__init__()
            self.layers = nn.ModuleList([nn.Identity() for _ in range(6)])
            self.emb = nn.Embedding(32, 16)

        def forward(self, input_ids, attention_mask=None):
            h = self.emb(input_ids)
            for layer in self.layers:
                h = layer(h)
            return (h,)

    mb = ModernBertEmbeddingModel(model_name="dummy", transformer=_DummyTransformer())
    assert mb.default_num_layers is None
    ids = torch.randint(0, 30, (2, 8))
    att = torch.ones_like(ids)
    errors = []

    def _worker(n_layers):
        try:
            for _ in range(10):
                out = mb(ids, att, num_layers=n_layers)
                assert out.shape == (2, 16)
        except Exception as exc:
            errors.append(exc)

    t1 = threading.Thread(target=_worker, args=(2,))
    t2 = threading.Thread(target=_worker, args=(None,))
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    assert not errors and len(mb.transformer.layers) == 6


def test_temporal_memory_ring_buffer_and_rollback_clean_step_state():
    """TemporalMemory ring buffer and SpecialistPipeline warm_step_state purge synthetic rollback contamination."""
    mem = TemporalMemory(feature_dim=1, max_len=8)
    ref = deque(maxlen=8)

    for v in range(1, 15):
        mem.push([float(v)])
        ref.append([float(v)])
    assert np.allclose(mem.get_numpy(), np.array(ref, dtype=np.float32))

    # Rollback across circular wrap-around boundary and push again
    mem.rollback(3)
    for _ in range(3):
        ref.pop()
    assert len(mem) == len(ref) == 5
    assert np.allclose(mem.get_numpy(), np.array(ref, dtype=np.float32))

    mem.push(99.0)
    ref.append([99.0])
    assert np.allclose(mem.get_numpy(), np.array(ref, dtype=np.float32))

    # End-to-end TrafficNode rollback -> warm_step_state parity against full-window encode
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    node = TrafficNodeFactory.create_traffic_node(
        MapNode(id="cam_sensor_1", x=0.0, y=0.0, node_type="priority"),
        device=device,
        historical_manager=None,
        graph_manager=None,
    )
    for val in [10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0]:
        node.step(val)
    for _ in range(4):
        node.ghost_step()
    assert node.fallback_steps == 4

    # Recover with real reading -> triggers rollback(4) + reset_step_state() + warm_step_state()
    node.step(26.0)
    assert node.fallback_steps == 0
    expected_emb = node.agent.predict(node.memory.get_numpy())
    assert np.allclose(node.last_embedding, expected_emb, atol=1e-5)

    # Next incremental O(1) step must also match full-window encode
    node.step(28.0)
    expected_next = node.agent.predict(node.memory.get_numpy())
    assert np.allclose(node.last_embedding, expected_next, atol=1e-5)


def test_snapshot_builder_immutable_zero_embedding_and_slm_clear_cache():
    """SnapshotBuilder reuses a read-only zero vector and LLMWorkerInstance clears cache safely."""
    app_state = MagicMock()
    app_state.get_all_nodes.return_value = [
        MapNode(id="G1", x=0.0, y=0.0, node_type="priority"),
        MapNode(id="G2", x=1.0, y=1.0, node_type="priority"),
    ]
    graph_mgr = MagicMock()
    graph_mgr.get_node.return_value = None
    graph_mgr.direct_edge_metrics = {}

    builder = SnapshotBuilder(app_state=app_state, graph_manager=graph_mgr, embedding_dim=32)
    snap = builder.gather_snapshot()
    assert snap["G1"]["embedding"] is snap["G2"]["embedding"]
    with pytest.raises(ValueError):
        snap["G1"]["embedding"][0] = 99.0

    worker = LLMWorkerInstance(model_id="dummy.gguf")
    res = worker.clear_cache()
    assert res["cache_cleared"] is True and res["loaded"] is False
