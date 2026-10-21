# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
import torch
import numpy as np

from src.utils.attention_utils import (
    get_sdpa_backend_info,
    fallback_math_attention,
    robust_sdpa
)
from src.models.itransformer import iTransformer
from src.models.itransformer_lite import iTransformerLite


def test_sdpa_backend_info():
    """Verify diagnostic utility reports environment capabilities."""
    info = get_sdpa_backend_info()
    assert "cuda_available" in info
    assert "flash_sdp" in info
    assert "mem_efficient_sdp" in info
    assert "math_sdp" in info


def test_fallback_math_attention_correctness():
    """Verify that fallback_math_attention produces valid outputs."""
    B, H, N, D = 2, 4, 16, 32
    Q = torch.randn(B, H, N, D)
    K = torch.randn(B, H, N, D)
    V = torch.randn(B, H, N, D)

    out = fallback_math_attention(Q, K, V)
    assert out.shape == (B, H, N, D)
    assert torch.isfinite(out).all()


def test_robust_sdpa_numerical_equivalence():
    """Verify that robust_sdpa matches math fallback within float tolerance."""
    B, H, N, D = 1, 2, 8, 16
    Q = torch.randn(B, H, N, D)
    K = torch.randn(B, H, N, D)
    V = torch.randn(B, H, N, D)

    out_sdpa = robust_sdpa(Q, K, V, enable_flash=True, enable_mem_efficient=True, enable_math=True)
    out_math = fallback_math_attention(Q, K, V)

    assert out_sdpa.shape == out_math.shape
    assert torch.allclose(out_sdpa, out_math, atol=1e-5)


def test_itransformer_with_accelerated_attention():
    """Verify that iTransformer forward pass runs cleanly with optimized attention."""
    num_variates = 12
    seq_len = 24
    pred_len = 1
    d_model = 32
    n_heads = 2
    spatial_dim = 16

    model = iTransformer(
        num_variates=num_variates,
        seq_len=seq_len,
        pred_len=pred_len,
        d_model=d_model,
        n_heads=n_heads,
        e_layers=1,
        spatial_dim=spatial_dim
    )
    model.eval()

    # Input: [Batch, Seq_Len, Num_Variates]
    x = torch.randn(2, seq_len, num_variates)
    spatial_ctx = torch.randn(2, num_variates, spatial_dim)

    with torch.no_grad():
        # Without spatial context
        out_no_spatial = model(x)
        assert out_no_spatial.shape == (2, pred_len, num_variates)
        assert torch.isfinite(out_no_spatial).all()

        # With spatial context (activates cross-attention)
        out_spatial = model(x, spatial_context=spatial_ctx)
        assert out_spatial.shape == (2, pred_len, num_variates)
        assert torch.isfinite(out_spatial).all()


def test_itransformer_lite_attention():
    """Verify iTransformerLite executes with need_weights=False without error."""
    num_sensors = 4
    seq_len = 30
    model = iTransformerLite(num_sensors=num_sensors, d_model=16, n_heads=2)
    model.eval()

    x = torch.randn(2, seq_len, num_sensors)
    with torch.no_grad():
        out = model(x)

    assert out.shape == (2, seq_len, 1)
    assert torch.isfinite(out).all()

