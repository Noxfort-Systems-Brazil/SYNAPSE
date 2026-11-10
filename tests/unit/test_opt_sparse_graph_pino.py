# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Unit and equivalence tests for Frente 1:
- O(|E|) sparse graph transitions & DiffusionGraphConv exact mathematical equivalence
- O(|E|) Chebyshev Graph Laplacian conv exact mathematical equivalence
- FusionPipeline 8-hop sparse harmonic diffusion vs. dense matrix fallback parity
- PINOTrafficFlow1D shared sparse Laplacian caching across 4 layers and eval cycles
- 2nd-order open-boundary finite differences in corridor LWR PDE
"""

import numpy as np
import pytest
import torch
import torch.nn as nn

from src.blocks.graph_blocks import DiffusionGraphConv
from src.blocks.spectral_blocks import GraphLaplacianSpectralConv
from src.factories.fuser_model_factory import FuserModelFactory
from src.models.pino_traffic import PINOTrafficFlow1D
from src.physics.pino_residuals import PINOTrafficResidualEngine
from src.utils.graph_utils import (
    compute_random_walk_transition_matrices,
    compute_sparse_transition_matrices,
)


def test_sparse_vs_dense_random_walk_transitions_and_diffusion():
    """Verifies exact numerical and gradient equivalence between O(|E|) sparse and dense DiffusionGraphConv."""
    torch.manual_seed(42)
    num_nodes = 8
    in_channels = 12
    out_channels = 10

    # Directed graph with asymmetric weights, dead-end sink (node 7), isolated node (node 6), and duplicate edge (0->1)
    edge_index = torch.tensor(
        [
            [0, 0, 0, 1, 2, 3, 4, 5],
            [1, 1, 2, 3, 3, 4, 5, 7],
        ],
        dtype=torch.long,
    )
    edge_weight = torch.tensor([0.5, 1.5, 0.8, 1.2, 0.7, 2.0, 1.1, 0.9], dtype=torch.float32)

    p_f, p_b = compute_random_walk_transition_matrices(
        num_nodes=num_nodes,
        edge_index=edge_index,
        edge_weight=edge_weight,
        damping_factor=0.85,
    )
    sparse_trans = compute_sparse_transition_matrices(
        num_nodes=num_nodes,
        edge_index=edge_index,
        edge_weight=edge_weight,
        damping_factor=0.85,
    )

    conv = DiffusionGraphConv(in_channels=in_channels, out_channels=out_channels, diffusion_steps=3)
    adp_adj = torch.softmax(torch.randn(num_nodes, num_nodes), dim=-1)

    x_dense = torch.randn(3, num_nodes, in_channels, requires_grad=True)
    x_sparse = x_dense.detach().clone().requires_grad_(True)

    out_dense = conv(x_dense, p_forward=p_f, p_backward=p_b, adaptive_adj=adp_adj)
    out_sparse = conv(x_sparse, adaptive_adj=adp_adj, sparse_transitions=sparse_trans)

    assert torch.allclose(out_sparse, out_dense, atol=1e-5)

    out_dense.sum().backward()
    out_sparse.sum().backward()
    assert x_dense.grad is not None and x_sparse.grad is not None
    assert torch.allclose(x_sparse.grad, x_dense.grad, atol=1e-5)

    # Disconnected fallback parity (empty edge_index)
    empty_edges = torch.empty((2, 0), dtype=torch.long)
    pf_empty, pb_empty = compute_random_walk_transition_matrices(num_nodes, empty_edges)
    sp_empty = compute_sparse_transition_matrices(num_nodes, empty_edges)
    assert torch.allclose(
        conv(x_dense.detach(), p_forward=pf_empty, p_backward=pb_empty),
        conv(x_dense.detach(), sparse_transitions=sp_empty),
        atol=1e-5,
    )


def test_sparse_vs_dense_chebyshev_spectral_conv():
    """Verifies exact numerical and gradient equivalence between O(|E|) sparse and dense Chebyshev Laplacian conv."""
    torch.manual_seed(7)
    num_nodes = 9
    in_dim = 16
    out_dim = 16

    # Asymmetric directed graph with duplicate edge (2->4) and isolated node (8)
    edge_index = torch.tensor(
        [
            [0, 1, 2, 2, 3, 4, 5, 6, 7],
            [1, 2, 4, 4, 0, 5, 6, 3, 2],
        ],
        dtype=torch.long,
    )
    edge_weight = torch.tensor([1.0, 2.5, 0.4, 1.3, 0.9, 1.7, 0.6, 1.1, 2.0], dtype=torch.float32)

    layer = GraphLaplacianSpectralConv(in_channels=in_dim, out_channels=out_dim, K=4)
    l_tilde = GraphLaplacianSpectralConv.compute_scaled_laplacian(
        num_nodes=num_nodes, edge_index=edge_index, edge_weight=edge_weight
    )
    sparse_lap = GraphLaplacianSpectralConv.compute_sparse_laplacian_edges(
        num_nodes=num_nodes, edge_index=edge_index, edge_weight=edge_weight
    )

    x_dense = torch.randn(2, num_nodes, in_dim, requires_grad=True)
    x_sparse = x_dense.detach().clone().requires_grad_(True)

    out_dense = layer(x_dense, l_tilde=l_tilde)
    out_sparse = layer(x_sparse, sparse_laplacian=sparse_lap)

    assert torch.allclose(out_sparse, out_dense, atol=1e-5)

    out_dense.mean().backward()
    out_sparse.mean().backward()
    assert x_dense.grad is not None and x_sparse.grad is not None
    assert torch.allclose(x_sparse.grad, x_dense.grad, atol=1e-5)


def test_fusion_pipeline_sparse_8hop_matches_dense_fallback():
    """Verifies that FusionPipeline 8-hop sparse harmonic diffusion matches the dense matrix path."""
    torch.manual_seed(11)
    num_nodes = 6
    seq_len = 12
    pipeline = FuserModelFactory.create_fusion_pipeline(
        num_variates=num_nodes,
        seq_len=seq_len,
        pred_len=1,
        d_model=32,
        n_heads=2,
        layers=1,
        spatial_dim=16,
    )

    history = np.random.uniform(15.0, 75.0, size=(seq_len, num_nodes)).astype(np.float32)
    mask = np.array([1.0, 0.0, 1.0, 0.0, 0.0, 0.0], dtype=np.float32)
    vel = np.array([55.0, 50.0, 48.0, 45.0, 42.0, 40.0], dtype=np.float32)
    edge_index = torch.tensor([[0, 1, 2, 3, 4, 2], [1, 2, 3, 4, 5, 0]], dtype=torch.long)

    out_sparse = pipeline.execute(
        current_history=history,
        observability_mask=mask,
        global_velocities=vel,
        edge_index=edge_index,
    )

    # Force fallback to dense p_f / p_b path by wrapping diffusion to hide last_sparse_transitions
    orig_diffusion = pipeline.diffusion

    class _DenseOnlyProxy(nn.Module):
        def __init__(self, inner: nn.Module):
            super().__init__()
            self.inner = inner

        def forward(self, *args, **kwargs):
            return self.inner(*args, **kwargs)

        @property
        def last_p_forward(self):
            return self.inner.last_p_forward

        @property
        def last_p_backward(self):
            return self.inner.last_p_backward

    pipeline.diffusion = _DenseOnlyProxy(orig_diffusion)
    try:
        out_dense = pipeline.execute(
            current_history=history,
            observability_mask=mask,
            global_velocities=vel,
            edge_index=edge_index,
        )
    finally:
        pipeline.diffusion = orig_diffusion

    assert np.allclose(out_sparse, out_dense, atol=1e-5)


def test_pino_traffic_shared_sparse_laplacian_caching_and_gradients(monkeypatch):
    """Verifies PINOTrafficFlow1D computes sparse Laplacian once across all 4 layers and caches across eval cycles."""
    pino = PINOTrafficFlow1D(in_channels=16, hidden_dim=32, num_layers=4, operator_mode="graph")
    edge_index = torch.tensor([[0, 1, 2, 3], [1, 2, 3, 0]], dtype=torch.long)
    x = torch.randn(2, 4, 16, requires_grad=True)

    orig_fn = GraphLaplacianSpectralConv.compute_sparse_laplacian_edges
    calls = {"count": 0}

    def _counted_fn(*args, **kwargs):
        calls["count"] += 1
        return orig_fn(*args, **kwargs)

    monkeypatch.setattr(GraphLaplacianSpectralConv, "compute_sparse_laplacian_edges", staticmethod(_counted_fn))

    # 1. Training mode: 1 computation shared across all 4 graph_spectral_layers (instead of 4)
    pino.train()
    refined, metrics = pino(x, edge_index=edge_index)
    assert calls["count"] == 1
    loss = refined.sum() + metrics["physics_residual"]
    loss.backward()
    for layer in pino.graph_spectral_layers:
        assert layer.weights.grad is not None

    # 2. Eval mode: 5 consecutive cycles compute sparse Laplacian only once total
    calls["count"] = 0
    pino.eval()
    with torch.no_grad():
        for _ in range(5):
            pino(x.detach(), edge_index=edge_index)
    assert calls["count"] == 1


def test_pino_residual_corridor_second_order_finite_differences():
    """
    Verifies that 2nd-order finite differences in corridor mode differentiate quadratic flow profiles
    q(x) = a*x^2 + b*x + c with zero truncation error across both interior and open boundary nodes.
    """
    engine = PINOTrafficResidualEngine()
    num_nodes = 8
    dx = 0.5
    dt = 1.0
    x_grid = torch.arange(num_nodes, dtype=torch.float32).view(1, num_nodes, 1) * dx

    # Quadratic flow q(x) = 3 x^2 + 4 x + 10 -> exact dq/dx = 6 x + 4
    a, b, c = 3.0, 4.0, 10.0
    q_est = a * (x_grid ** 2) + b * x_grid + c
    exact_dq_dx = 2.0 * a * x_grid + b

    # Choose k_prev and k_next so centered dk/dt = -exact_dq_dx -> dk/dt + dq/dx == 0 everywhere!
    k_est = torch.full_like(q_est, 25.0)
    k_prev = k_est + exact_dq_dx * dt
    k_next = k_est - exact_dq_dx * dt
    v_est = torch.full_like(q_est, 50.0)
    v_free = torch.full_like(q_est, 60.0)
    k_jam = torch.full_like(q_est, 120.0)

    res = engine.compute_residuals(
        k_est=k_est,
        v_est=v_est,
        q_est=q_est,
        v_free=v_free,
        k_jam=k_jam,
        edge_index=None,
        operator_mode="corridor",
        dt=dt,
        dx=dx,
        k_prev=k_prev,
        k_next=k_next,
    )

    assert res["temporal_continuity_active"] is True
    assert float(res["res_lwr_pde"].item()) < 1e-5
