# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Unit and equivalence tests for Frente 2:
- PIDeepONet TrunkNet basis and canonical grid eval-mode caching with automatic invalidation
- ImputerPipeline vectorized mini-batch 2D/3D NaN imputation without inner-loop CUDA syncs
"""

import numpy as np
import pytest
import torch

from src.models.pi_deeponet import PIDeepONet
from src.pipeline.imputer_pipeline import ImputerPipeline


def test_pi_deeponet_trunk_eval_cache_and_invalidation(monkeypatch):
    """Verifies TrunkNet is evaluated once in eval() mode and invalidated upon train() or state_dict load."""
    model = PIDeepONet(feature_dim=3, seq_len=16, p_latent=16, hidden_dim=32)
    model.eval()

    orig_trunk_forward = model.trunk.forward
    calls = {"count": 0}

    def _counted_trunk(y):
        calls["count"] += 1
        return orig_trunk_forward(y)

    monkeypatch.setattr(model.trunk, "forward", _counted_trunk)

    # 1. Canonical grid (y=None): 4 calls -> 1 trunk evaluation
    with torch.no_grad():
        outs = [model(torch.randn(4, 16, 3)) for _ in range(4)]
    assert calls["count"] == 1
    assert outs[0].shape == (4, 16, 3)

    # 2. Explicit static street query coordinates: 4 calls -> 1 trunk evaluation
    calls["count"] = 0
    static_coords = torch.rand(10, 2)
    with torch.no_grad():
        for _ in range(4):
            out_q = model(torch.randn(3, 16, 3), y=static_coords)
    assert calls["count"] == 1
    assert out_q.shape == (3, 10, 3)

    # 3. Switching to train() invalidates cache
    model.train()
    assert len(model._cached_canonical_trunk) == 0
    assert model._last_query_trunk is None

    # 4. Loading new state_dict invalidates eval cache immediately
    model.eval()
    u_fixed = torch.randn(2, 16, 3)
    with torch.no_grad():
        before = model(u_fixed).clone()
    state = {k: v.clone() for k, v in model.state_dict().items()}
    for k in state:
        if k.startswith("trunk."):
            state[k] = state[k] + 0.25
    model.load_state_dict(state)
    calls["count"] = 0
    with torch.no_grad():
        after = model(u_fixed)
    assert calls["count"] == 1
    assert not torch.allclose(before, after)


def test_imputer_pipeline_vectorized_2d_and_3d_no_empty_cache(monkeypatch):
    """Verifies vectorized 2D/3D NaN reconstruction preserves observed entries and never calls empty_cache in loops."""
    empty_cache_calls = {"count": 0}
    monkeypatch.setattr(
        torch.cuda,
        "empty_cache",
        lambda: empty_cache_calls.__setitem__("count", empty_cache_calls["count"] + 1),
    )

    pipeline = ImputerPipeline(feature_dim=3, seq_len=16, d_model=16, d_ff=32, device=torch.device("cpu"))

    # 2D sequence with non-multiple tail length (65 = 4 * 16 + 1)
    seq_2d = np.random.uniform(10.0, 70.0, size=(65, 3)).astype(np.float32)
    seq_2d[3:7, 0] = np.nan
    seq_2d[60:64, 2] = np.nan
    obs_mask_2d = ~np.isnan(seq_2d)

    rec_2d = pipeline.reconstruct(seq_2d, chunk_size=32)
    assert rec_2d.shape == seq_2d.shape
    assert not np.isnan(rec_2d).any()
    assert np.allclose(rec_2d[obs_mask_2d], seq_2d[obs_mask_2d])

    # 3D batch sequence
    seq_3d = np.random.uniform(10.0, 70.0, size=(6, 16, 3)).astype(np.float32)
    seq_3d[:, 5:8, 1] = np.nan
    obs_mask_3d = ~np.isnan(seq_3d)

    rec_3d = pipeline.reconstruct(seq_3d)
    assert rec_3d.shape == seq_3d.shape
    assert not np.isnan(rec_3d).any()
    assert np.allclose(rec_3d[obs_mask_3d], seq_3d[obs_mask_3d])
    assert empty_cache_calls["count"] == 0
