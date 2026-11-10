# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Unit and equivalence tests for Frente 4:
- AdaptivePhysicsLossBalancer cosine curriculum warmup ramp and EMA stiffness balancing
- FuserTrainer non-zero statistical spatial context projection and balancer progression
- AuditorTrainer adaptive training loss and threshold calibration contract
- CorrectorTrainer adaptive loss balancing and device migration
"""

import numpy as np
import pytest
import torch

from src.factories.fuser_model_factory import FuserModelFactory
from src.models.pi_dvae_tcn import PIDVAETCN
from src.physics.adaptive_loss_balancer import AdaptivePhysicsLossBalancer
from src.pipeline.auditor_pipeline import AuditorPipeline
from src.trainer.auditor_trainer import AuditorTrainer
from src.trainer.corrector_trainer import CorrectorTrainer
from src.trainer.fuser_trainer import FuserTrainer


def test_adaptive_physics_loss_balancer_warmup_and_stiffness_clamping():
    """Verifies cosine curriculum warmup, 1000x stiffness normalization, scale bounds, and NaN safety."""
    balancer = AdaptivePhysicsLossBalancer(
        base_weight=0.1,
        warmup_steps=10,
        warmup_start_factor=0.2,
        ema_decay=0.9,
        min_scale=1e-4,
        max_scale=10.0,
    )

    # 1. Monotonic warmup ramp from 0.2 -> 1.0
    factors = [balancer.compute_warmup_factor(s) for s in range(1, 12)]
    assert np.isclose(factors[0], 0.2)
    assert np.isclose(factors[9], 1.0)
    assert np.isclose(factors[10], 1.0)
    assert all(factors[i] <= factors[i + 1] for i in range(len(factors) - 1))

    # 2. Stiffness balancing when L_phys = 1000 * L_data (e.g. macroscopic veh/h residuals vs normalized MSE)
    data_loss = torch.tensor(0.5, requires_grad=True)
    phys_loss = torch.tensor(500.0, requires_grad=True)  # 1000x larger!
    for _ in range(12):
        weighted = balancer(data_loss, phys_loss)

    # After 10 warmup steps (warmup=1.0), scale = 0.5 / 500 = 1e-3 -> weighted = 0.1 * 1e-3 * 500 = 0.05!
    assert isinstance(weighted, torch.Tensor)
    assert np.isclose(float(weighted.item()), 0.05, rtol=1e-2)
    weighted.backward()
    assert phys_loss.grad is not None and torch.isfinite(phys_loss.grad)

    # 3. Extreme stiffness clamps at min_scale
    balancer.reset()
    for _ in range(12):
        _ = balancer(torch.tensor(0.1), torch.tensor(1e7))
    assert np.isclose(balancer.last_scale, 1e-4)

    # 4. Non-finite physics loss contributes 0.0 safely without corrupting gradients
    nan_phys = torch.tensor(float("nan"), requires_grad=True)
    safe_out = balancer(torch.tensor(1.0), nan_phys)
    assert float(safe_out.item()) == 0.0


def test_trainers_adaptive_balancer_and_spatial_context_integration():
    """Verifies FuserTrainer, AuditorTrainer, and CorrectorTrainer integrate AdaptivePhysicsLossBalancer cleanly."""
    # 1. FuserTrainer: non-zero statistical spatial context + adaptive balancer step
    fuser_pipe = FuserModelFactory.create_fusion_pipeline(
        num_variates=4, seq_len=12, pred_len=1, d_model=16, n_heads=2, layers=1, spatial_dim=10
    )
    fuser_trainer = FuserTrainer(composite_model=fuser_pipe.module_dict, spatial_dim=10, physics_weight=0.05)
    x_seq = torch.randn(3, 12, 4) * 20.0 + 40.0
    spatial_ctx = fuser_trainer._extract_spatial_context(x_seq)
    assert spatial_ctx.shape == (3, 4, 10)
    assert float(spatial_ctx.abs().sum().item()) > 0.0

    y_seq = torch.randn(3, 1, 4)
    edges = torch.tensor([[0, 1, 2], [1, 2, 3]], dtype=torch.long)
    f_loss = fuser_trainer.train_step((x_seq, y_seq, edges))
    assert np.isfinite(f_loss)
    assert fuser_trainer.loss_balancer.step_count == 1

    # 2. AuditorTrainer: adaptive loss balancing + nominal calibration threshold contract
    active_dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    auditor_pipe = AuditorPipeline(input_len=32, J=2, latent_dim=16, device=active_dev)
    auditor_trainer = AuditorTrainer(model=auditor_pipe.model, physics_weight=0.5, device=active_dev)
    a_loss = auditor_trainer.train_step(torch.rand(4, 32) * 40.0)
    assert np.isfinite(a_loss)
    assert auditor_trainer.loss_balancer.step_count == 1
    assert auditor_trainer.calibrator.threshold > 0.0

    # Verify explicit CPU transfer parity as well
    auditor_trainer.to("cpu")
    a_loss_cpu = auditor_trainer.train_step(torch.rand(4, 32) * 40.0)
    assert np.isfinite(a_loss_cpu)
    assert auditor_trainer.loss_balancer.step_count == 2

    # 3. CorrectorTrainer: adaptive loss balancing
    corrector_model = PIDVAETCN(input_channels=2, hidden_channels=16, latent_channels=8)
    corrector_trainer = CorrectorTrainer(model=corrector_model, physics_weight=0.1, device=active_dev)
    c_loss = corrector_trainer.train_step(np.random.uniform(15.0, 60.0, size=(4, 16, 2)).astype(np.float32))
    assert np.isfinite(c_loss)
    assert corrector_trainer.loss_balancer.step_count == 1
