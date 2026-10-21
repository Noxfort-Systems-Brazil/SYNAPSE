# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import torch
import torch.nn as nn
import torch.nn.functional as F
from src.interfaces.physics import IPhysicsConstraint


class NonNegativityBoundsConstraint(nn.Module):
    """
    Penalizes negative values for strictly non-negative physical quantities (q >= 0, v >= 0, rho >= 0).
    Residual: mean(ReLU(-x)^2)
    """

    def __init__(self, penalty_scale: float = 1.0):
        super().__init__()
        self.penalty_scale = penalty_scale

    def compute_residual(self, state: torch.Tensor, **kwargs) -> torch.Tensor:
        """
        Args:
            state: Tensor of physical states [Batch, Channels, SeqLen] or [Batch, SeqLen].
        Returns:
            loss_bounds: Scalar penalty tensor.
        """
        loss = torch.mean(torch.relu(-state) ** 2)
        return self.penalty_scale * loss


class KinematicAccelerationConstraint(nn.Module):
    """
    Enforces physically plausible vehicle kinematics by penalizing acceleration / deceleration
    exceeding realistic thresholds: |dv/dt| <= max_acceleration.
    Residual: mean(ReLU(|dv/dt| - max_acceleration)^2)
    """

    def __init__(self, max_acceleration: float = 10.0, dt: float = 1.0, penalty_scale: float = 1.0):
        super().__init__()
        self.max_acceleration = max_acceleration
        self.dt = dt
        self.penalty_scale = penalty_scale

    def compute_residual(self, velocity_sequence: torch.Tensor, **kwargs) -> torch.Tensor:
        """
        Args:
            velocity_sequence: Tensor of velocities [..., SeqLen]
        Returns:
            loss_kinematics: Scalar penalty tensor.
        """
        device = velocity_sequence.device
        seq_len = velocity_sequence.shape[-1]
        
        if seq_len <= 1:
            return torch.tensor(0.0, device=device)
            
        dv = velocity_sequence[..., 1:] - velocity_sequence[..., :-1]
        accel = torch.abs(dv) / self.dt
        loss = torch.mean(torch.relu(accel - self.max_acceleration) ** 2)
        return self.penalty_scale * loss


class TemporalSmoothnessConstraint(nn.Module):
    """
    Penalizes high-frequency unphysical sensor jitter / spikes using Smooth L1 (Total Variation)
    on consecutive time steps.
    """

    def __init__(self, penalty_scale: float = 1.0):
        super().__init__()
        self.penalty_scale = penalty_scale

    def compute_residual(self, sequence: torch.Tensor, **kwargs) -> torch.Tensor:
        """
        Args:
            sequence: Tensor [..., SeqLen]
        Returns:
            loss_smooth: Scalar smoothness penalty tensor.
        """
        device = sequence.device
        seq_len = sequence.shape[-1]
        
        if seq_len <= 1:
            return torch.tensor(0.0, device=device)
            
        loss = torch.mean(F.smooth_l1_loss(sequence[..., 1:], sequence[..., :-1]))
        return self.penalty_scale * loss
