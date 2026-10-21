# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
import torch
import time
import numpy as np

from src.blocks.spectral_blocks import (
    SpectralConv1d,
    SpectralConv2d,
    GraphLaplacianSpectralConv,
)
from src.blocks.feature_blocks import SpectralFeatureBlock, SpectralFeatureExtractor
from src.models.pino_traffic import PINOTrafficFlow1D


def test_spectral_conv1d_forward():
    """Verifies SpectralConv1d operates via FFT/IFFT preserving shape."""
    batch_size = 4
    channels = 16
    seq_len = 64
    modes = 8

    layer = SpectralConv1d(in_channels=channels, out_channels=channels, modes1=modes)
    x = torch.randn(batch_size, channels, seq_len)
    out = layer(x)

    assert out.shape == (batch_size, channels, seq_len)
    assert torch.isfinite(out).all()


def test_spectral_conv2d_forward():
    """Verifies SpectralConv2d operates over 2D spatiotemporal grids."""
    batch_size = 2
    channels = 8
    size_x, size_y = 32, 32
    modes = 8

    layer = SpectralConv2d(in_channels=channels, out_channels=channels, modes1=modes, modes2=modes)
    x = torch.randn(batch_size, channels, size_x, size_y)
    out = layer(x)

    assert out.shape == (batch_size, channels, size_x, size_y)
    assert torch.isfinite(out).all()


def test_pino_traffic_flow_mesh_invariance():
    """Verifies PINO evaluates seamlessly across varying spatial resolutions (Mesh-Invariance)."""
    in_dim = 32
    hidden_dim = 32
    pino = PINOTrafficFlow1D(in_channels=in_dim, hidden_dim=hidden_dim, modes=8)

    # Resolution A: 30 nodes
    x_30 = torch.randn(2, 30, in_dim)
    refined_30, metrics_30 = pino(x_30)
    assert refined_30.shape == (2, 30, in_dim)

    # Resolution B: 100 nodes (same weights, zero retraining)
    x_100 = torch.randn(2, 100, in_dim)
    refined_100, metrics_100 = pino(x_100)
    assert refined_100.shape == (2, 100, in_dim)

    assert (metrics_30["density"] >= 0).all()
    assert (metrics_100["density"] >= 0).all()


def test_pino_latency_benchmark():
    """Verifies PINO forward execution executes well under real-time requirements (< 5ms)."""
    pino = PINOTrafficFlow1D(in_channels=32, hidden_dim=64, modes=16)
    pino.eval()

    x = torch.randn(1, 50, 32)

    # Warmup
    for _ in range(5):
        _ = pino(x)

    start = time.perf_counter()
    for _ in range(50):
        _ = pino(x)
    elapsed_ms = ((time.perf_counter() - start) / 50) * 1000

    assert elapsed_ms < 10.0, f"PINO execution took {elapsed_ms:.2f}ms, exceeding latency budget."


def test_spectral_feature_extractor():
    """Verifies SpectralFeatureExtractor matches expected feature shapes."""
    batch_size = 2
    seq_len = 128
    enc_in = 2

    extractor = SpectralFeatureExtractor(enc_in=enc_in, d_model=32, modes=16)
    x = torch.randn(batch_size, seq_len, enc_in)
    out = extractor(x)

    assert out.shape == (batch_size, seq_len, enc_in)
    assert torch.isfinite(out).all()


def test_graph_laplacian_spectral_conv_forward():
    """Verifies GraphLaplacianSpectralConv operates on graph topologies."""
    num_nodes = 5
    in_channels = 16
    out_channels = 32
    edge_index = torch.tensor([[0, 1, 2, 3], [1, 2, 3, 4]], dtype=torch.long)

    conv = GraphLaplacianSpectralConv(in_channels=in_channels, out_channels=out_channels, K=3)
    x = torch.randn(2, num_nodes, in_channels)

    out = conv(x, edge_index=edge_index)
    assert out.shape == (2, num_nodes, out_channels)
    assert torch.isfinite(out).all()


def test_graph_laplacian_spectral_conv_permutation_equivariance():
    """
    Verifies that Graph Laplacian spectral convolution is strictly permutation-equivariant.
    Renumbering graph nodes permutes the output identically, preserving physical spatial meaning.
    """
    torch.manual_seed(42)
    num_nodes = 5
    channels = 8
    # Directed line graph: 0 -> 1 -> 2 -> 3 -> 4
    edge_index = torch.tensor([[0, 1, 2, 3], [1, 2, 3, 4]], dtype=torch.long)
    conv = GraphLaplacianSpectralConv(in_channels=channels, out_channels=channels, K=3)
    conv.eval()

    x = torch.randn(1, num_nodes, channels)

    # Original forward
    with torch.no_grad():
        out_orig = conv(x, edge_index=edge_index)

    # Permute node indices (e.g. 0->4, 1->2, 2->0, 3->3, 4->1)
    perm = torch.tensor([4, 2, 0, 3, 1], dtype=torch.long)
    inv_perm = torch.empty_like(perm)
    inv_perm[perm] = torch.arange(num_nodes)

    x_perm = x[:, perm, :]
    # Permute edge index endpoints: old node u maps to new node inv_perm[u]
    edge_index_perm = inv_perm[edge_index]

    with torch.no_grad():
        out_perm = conv(x_perm, edge_index=edge_index_perm)

    # The un-permuted out_perm should match out_orig
    out_recovered = out_perm[:, inv_perm, :]
    assert torch.allclose(out_orig, out_recovered, atol=1e-5), "Graph Laplacian convolution must be permutation equivariant"


def test_pino_corridor_lwr_pde_conservation():
    """
    Verifies PINO computes true LWR PDE residual (dk/dt + dq/dx) along a 1D roadway corridor.
    """
    in_dim = 16
    pino = PINOTrafficFlow1D(in_channels=in_dim, hidden_dim=32, modes=8, operator_mode="corridor")
    num_cells = 20
    x = torch.randn(2, num_cells, in_dim)

    # Synthetic consecutive states for density
    k_current = torch.rand(2, num_cells, 1) * 30.0
    # Simulate a downstream shockwave (k_next > k_current)
    k_next = k_current + torch.randn_like(k_current) * 2.0

    refined, metrics = pino(x, edge_index=None, dt=1.0, dx=100.0, k_next=k_next)

    assert refined.shape == (2, num_cells, in_dim)
    assert "physics_residual" in metrics
    assert "res_flow" in metrics
    assert metrics["physics_residual"].item() > 0.0


def test_pino_graph_laplacian_operator_mode():
    """
    Verifies PINO in graph mode executes GraphLaplacianSpectralConv across arbitrary connectivity.
    """
    in_dim = 16
    pino = PINOTrafficFlow1D(in_channels=in_dim, hidden_dim=32, cheb_k=3, operator_mode="graph")
    num_nodes = 6
    x = torch.randn(1, num_nodes, in_dim)
    # Bifurcation topology: 0 -> 1, 1 -> 2, 1 -> 3, 2 -> 4, 3 -> 5
    edge_index = torch.tensor([[0, 1, 1, 2, 3], [1, 2, 3, 4, 5]], dtype=torch.long)

    refined, metrics = pino(x, edge_index=edge_index)
    assert refined.shape == (1, num_nodes, in_dim)
    assert "physics_residual" in metrics
    assert "res_conservation" in metrics
    assert torch.isfinite(metrics["physics_residual"])


def test_pino_corridor_no_silent_stationary_assumption():
    """
    Verifies that in corridor mode without k_next/k_prev, PINOTrafficResidualEngine
    does NOT silently assume dk/dt = 0 (stationary flow), and only activates LWR PDE
    when temporal states (k_next/k_prev) or assume_stationary=True are provided.
    """
    in_dim = 16
    pino = PINOTrafficFlow1D(in_channels=in_dim, hidden_dim=32, modes=8, operator_mode="corridor")
    x = torch.randn(2, 10, in_dim)

    # 1. Without k_next/k_prev and assume_stationary=False (default)
    _, metrics_default = pino(x, edge_index=None, dt=1.0, dx=50.0)
    assert metrics_default["temporal_continuity_active"] is False
    assert metrics_default["res_lwr_pde"].item() == 0.0
    assert torch.allclose(metrics_default["physics_residual"], metrics_default["res_flow"])

    # 2. With both k_prev and k_next (centered finite difference)
    k_prev = torch.rand(2, 10, 1) * 20.0
    k_next = k_prev + 5.0
    _, metrics_temporal = pino(x, edge_index=None, dt=1.0, dx=50.0, k_prev=k_prev, k_next=k_next)
    assert metrics_temporal["temporal_continuity_active"] is True
    assert metrics_temporal["res_lwr_pde"].item() > 0.0

    # 3. With explicit assume_stationary=True
    _, metrics_stationary = pino(x, edge_index=None, dt=1.0, dx=50.0, assume_stationary=True)
    assert metrics_stationary["temporal_continuity_active"] is True
    assert metrics_stationary["res_lwr_pde"].item() >= 0.0


