# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Unit and equivalence tests for Frente 3:
- Hardware AMP dtype (BF16/FP16) selection, GradScaler necessity, and in-place torch.compile safety
- SpatialGraphConservation zero GPU-to-CPU .item() syncs and bfloat16 AMP compatibility
- TensorBuilder pre-allocated host buffer reuse across cycles and dynamic topology resizing
"""

from types import SimpleNamespace
import numpy as np
import pytest
import torch
import torch.nn as nn

from src.engine.tensor_builder import TensorBuilder
from src.physics.continuum import SpatialGraphConservation
from src.utils.hardware import (
    get_optimal_amp_dtype,
    maybe_compile_module,
    requires_grad_scaler,
)


def test_hardware_amp_helpers_and_inplace_compile(monkeypatch):
    """Verifies BF16/FP16 AMP selection, GradScaler policy, and state_dict preservation under in-place compile."""
    assert get_optimal_amp_dtype("cpu") == torch.float32
    assert requires_grad_scaler("cpu", torch.float32) is False
    assert requires_grad_scaler("cuda", torch.bfloat16) is False
    assert requires_grad_scaler("cuda", torch.float16) is True

    class _TinyBackbone(nn.Module):
        def __init__(self):
            super().__init__()
            self.fc = nn.Linear(4, 4)

        def forward(self, x):
            return torch.relu(self.fc(x))

    mod = _TinyBackbone()
    orig_keys = set(mod.state_dict().keys())

    monkeypatch.setenv("SYNAPSE_TORCH_COMPILE", "0")
    mod_off = maybe_compile_module(mod, device="cpu")
    assert mod_off is mod
    assert not getattr(mod, "_synapse_compiled", False)

    monkeypatch.setenv("SYNAPSE_TORCH_COMPILE", "1")
    mod_on = maybe_compile_module(mod, device="cpu")
    assert mod_on is mod
    assert isinstance(mod_on, _TinyBackbone)
    assert set(mod_on.state_dict().keys()) == orig_keys


def test_spatial_graph_conservation_no_item_sync_and_bfloat16():
    """Verifies SpatialGraphConservation handles loop graphs (num_nodes == num_edges) and bfloat16 tensors cleanly."""
    cons = SpatialGraphConservation(penalty_scale=1.0)
    # 4-node directed cycle (num_nodes == num_edges == 4)
    edge_index = torch.tensor([[0, 1, 2, 3], [1, 2, 3, 0]], dtype=torch.long)

    flow_bf16 = torch.tensor([[100.0, 100.0, 100.0, 100.0]], dtype=torch.bfloat16, requires_grad=True)
    loss_balanced = cons(flow_bf16, edge_index=edge_index)
    assert torch.isfinite(loss_balanced)
    assert float(loss_balanced.float().item()) < 1e-3
    loss_balanced.backward()
    assert flow_bf16.grad is not None

    flow_imbalanced = torch.tensor([[120.0, 60.0, 120.0, 60.0]], dtype=torch.bfloat16)
    loss_imbalanced = cons(flow_imbalanced, edge_index=edge_index)
    assert float(loss_imbalanced.float().item()) > 10.0


def test_tensor_builder_buffer_reuse_and_dynamic_topology_resize():
    """Verifies TensorBuilder reuses pre-allocated host buffers across 1Hz cycles and resizes on topology changes."""

    class _MockMemory:
        def __init__(self, arr: np.ndarray):
            self._arr = arr

        def get_numpy(self) -> np.ndarray:
            return self._arr

    nodes = {
        f"n{i}": SimpleNamespace(memory=_MockMemory(np.linspace(10.0, 20.0 + i, 15, dtype=np.float32)))
        for i in range(4)
    }

    class _MockGraphManager:
        def __init__(self):
            self.ordered_ids = ["n0", "n1", "n2", "n3"]
            self.edge_index = torch.tensor([[0, 1, 2], [1, 2, 3]], dtype=torch.long)
            self.app_state = None

        def get_ordered_node_ids(self):
            return self.ordered_ids

        def get_node(self, nid: str):
            return nodes.get(nid)

    gm = _MockGraphManager()
    coord = SimpleNamespace(conv1=SimpleNamespace(in_channels=8))
    builder = TensorBuilder(device=torch.device("cpu"), coordinator_model=coord, graph_manager=gm)  # type: ignore[arg-type]

    snap1 = {"n0": {"value": 42.0, "type": "real", "embedding": np.ones(8, dtype=np.float32)}}
    x_sp1, e1, x_t1, m1, v1 = builder.prepare_tensors(snap1)
    buf_ptr_1 = builder._spatial_cpu.data_ptr()  # type: ignore[union-attr]

    snap2 = {"n0": {"value": 55.0, "type": "real", "embedding": np.full(8, 2.0, dtype=np.float32)}}
    x_sp2, e2, x_t2, m2, v2 = builder.prepare_tensors(snap2)
    buf_ptr_2 = builder._spatial_cpu.data_ptr()  # type: ignore[union-attr]

    # Internal host buffer is reused across cycles, while returned CPU tensors do not alias/overwrite snap1
    assert buf_ptr_1 == buf_ptr_2
    assert e1.data_ptr() == e2.data_ptr()
    assert float(x_sp1[0, 0].item()) == 1.0
    assert float(x_sp2[0, 0].item()) == 2.0
    assert float(m2[0].item()) == 1.0 and float(m2[1].item()) == 0.0
    assert x_t2.shape == (TensorBuilder.TARGET_SEQ_LEN, 4)

    # Dynamic topology expansion: add 5th node
    nodes["n4"] = SimpleNamespace(memory=_MockMemory(np.ones(70, dtype=np.float32) * 33.0))
    gm.ordered_ids.append("n4")
    gm.edge_index = torch.tensor([[0, 1, 2, 3], [1, 2, 3, 4]], dtype=torch.long)

    x_sp3, e3, x_t3, m3, _ = builder.prepare_tensors({"n4": {"value": 33.0, "type": "real"}})
    assert x_sp3.shape == (5, 8)
    assert x_t3.shape == (TensorBuilder.TARGET_SEQ_LEN, 5)
    assert e3.shape == (2, 4)
    assert float(m3[4].item()) == 1.0
