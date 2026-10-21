# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
import torch
import numpy as np

from src.models.pi_deeponet import PIDeepONet, BranchNet, TrunkNet


def test_pi_deeponet_branch_and_trunk_forward():
    """Verifies BranchNet and TrunkNet output valid latent shapes."""
    batch_size = 4
    num_sensors = 6
    p_latent = 32
    num_queries = 20

    branch = BranchNet(in_features=num_sensors, p_latent=p_latent)
    trunk = TrunkNet(coord_dim=2, p_latent=p_latent)

    u = torch.randn(batch_size, num_sensors)
    y = torch.rand(batch_size, num_queries, 2)

    b = branch(u)
    t = trunk(y)

    assert b.shape == (batch_size, p_latent)
    assert t.shape == (batch_size, num_queries, p_latent)
    assert torch.isfinite(b).all()
    assert torch.isfinite(t).all()


def test_pi_deeponet_continuous_zero_shot_evaluation():
    """Verifies PIDeepONet can evaluate at arbitrary continuous (x, t) query points."""
    batch_size = 2
    num_sensors = 5
    out_channels = 3  # [density, speed, flow]

    model = PIDeepONet(sensor_dim=num_sensors, p_latent=32, out_channels=out_channels)

    # 1. Sparse sensor readings
    u = torch.randn(batch_size, num_sensors).abs()

    # 2. Arbitrary query points (e.g. 50 continuous points along road segment)
    y_queries = torch.rand(batch_size, 50, 2)

    output, residuals = model(u, y=y_queries, return_physics_residual=True)

    assert output.shape == (batch_size, 50, out_channels)
    # Non-negativity check
    assert (output >= 0.0).all(), "Density, speed, and flow must be non-negative."
    assert "conservation_residual" in residuals
    assert residuals["conservation_residual"].item() >= 0.0


def test_pi_deeponet_sequence_imputation_mode():
    """Verifies PIDeepONet behaves as a drop-in 3D sequence operator for ImputerPipeline."""
    batch_size = 8
    seq_len = 24
    feature_dim = 4

    model = PIDeepONet(feature_dim=feature_dim, seq_len=seq_len, p_latent=32)

    # Sequence input: [Batch, SeqLen, Channels]
    x_seq = torch.randn(batch_size, seq_len, feature_dim)
    reconstructed = model(x_seq)

    assert reconstructed.shape == (batch_size, seq_len, feature_dim)
    assert not torch.isnan(reconstructed).any()
