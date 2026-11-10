# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Adaptive Physics-Informed Loss Balancer with Curriculum Warmup and EMA Magnitude Scaling.

Resolves the classic multi-task stiffness between normalized empirical MSE losses (O(1e-2..1e0))
and macroscopic hydrodynamic PDE residuals (LWR / Kirchhoff conservation in veh/h, O(1e2..1e6))
with zero second-backward computational overhead.
"""

import math
from typing import Optional, Union

import torch


class AdaptivePhysicsLossBalancer:
    """
    Dynamically balances empirical data loss and physics-informed PDE residuals.

    Features:
    1. **Curriculum Warmup:** Smooth cosine ramp from `warmup_start_factor` to `1.0` over
       `warmup_steps` iterations so neural backbones stabilize empirical reconstruction before
       strict PDE enforcement.
    2. **EMA Magnitude Balancing (Zero Second-Backward Cost):** Tracks exponential moving
       averages of `|L_data|` and `|L_phys|` on detached scalars without CPU-GPU `.item()`
       synchronizations, scaling the physics residual into a bounded relative range
       `[min_scale, max_scale]`.
    """

    def __init__(
        self,
        base_weight: float = 0.1,
        warmup_steps: int = 20,
        warmup_start_factor: float = 0.1,
        ema_decay: float = 0.95,
        min_scale: float = 1e-4,
        max_scale: float = 10.0,
        eps: float = 1e-6,
    ) -> None:
        self.base_weight = float(base_weight)
        self.warmup_steps = max(0, int(warmup_steps))
        self.warmup_start_factor = float(min(max(warmup_start_factor, 0.0), 1.0))
        self.ema_decay = float(min(max(ema_decay, 0.0), 0.9999))
        self.min_scale = float(max(min_scale, 0.0))
        self.max_scale = float(max(max_scale, self.min_scale))
        self.eps = float(max(eps, 1e-12))

        self._step_count: int = 0
        self._ema_data: Optional[torch.Tensor] = None
        self._ema_phys: Optional[torch.Tensor] = None
        self._last_scale: Optional[torch.Tensor] = None
        self._last_effective_weight: Optional[torch.Tensor] = None

    def reset(self) -> None:
        """Resets curriculum step counter and exponential moving average states."""
        self._step_count = 0
        self._ema_data = None
        self._ema_phys = None
        self._last_scale = None
        self._last_effective_weight = None

    @property
    def step_count(self) -> int:
        """Number of optimization steps processed so far."""
        return self._step_count

    @property
    def last_scale(self) -> float:
        """Most recent clamped EMA relative magnitude scale factor."""
        if self._last_scale is None:
            return 1.0
        return float(self._last_scale.item())

    @property
    def last_effective_weight(self) -> float:
        """Most recent effective physics loss multiplier `base_weight * warmup * scale`."""
        if self._last_effective_weight is None:
            return self.base_weight * self.compute_warmup_factor(1)
        return float(self._last_effective_weight.item())

    def compute_warmup_factor(self, step: Optional[int] = None) -> float:
        """
        Computes smooth cosine curriculum warmup factor in `[warmup_start_factor, 1.0]`.
        `step` is 1-indexed (step=1 yields `warmup_start_factor`; step>=warmup_steps yields `1.0`).
        """
        if self.warmup_steps <= 1:
            return 1.0

        curr_step = self._step_count if step is None else int(step)
        if curr_step <= 1:
            return self.warmup_start_factor
        if curr_step >= self.warmup_steps:
            return 1.0

        progress = (curr_step - 1) / float(self.warmup_steps - 1)
        cosine_ramp = 0.5 * (1.0 - math.cos(math.pi * progress))
        return self.warmup_start_factor + (1.0 - self.warmup_start_factor) * cosine_ramp

    def balance(
        self,
        data_loss: torch.Tensor,
        physics_loss: Union[torch.Tensor, float, int],
    ) -> Union[torch.Tensor, float]:
        """
        Computes the adaptively weighted physics loss contribution `lambda_eff * L_phys`.
        """
        self._step_count += 1
        warmup = self.compute_warmup_factor(self._step_count)

        if self.base_weight <= 0.0:
            if isinstance(physics_loss, torch.Tensor):
                zero_w = torch.zeros((), device=physics_loss.device, dtype=torch.float32)
                self._last_scale = torch.ones_like(zero_w)
                self._last_effective_weight = zero_w
                return torch.nan_to_num(physics_loss, nan=0.0, posinf=0.0, neginf=0.0) * 0.0
            self._last_scale = torch.tensor(1.0)
            self._last_effective_weight = torch.tensor(0.0)
            return 0.0

        if not isinstance(physics_loss, torch.Tensor):
            phys_float = float(physics_loss)
            if phys_float == 0.0 or not math.isfinite(phys_float):
                self._last_scale = torch.tensor(1.0)
                self._last_effective_weight = torch.tensor(self.base_weight * warmup)
                return 0.0
            physics_loss = torch.tensor(phys_float, device=data_loss.device, dtype=data_loss.dtype)

        with torch.no_grad():
            d_val = data_loss.detach().float().mean().abs()
            p_val = physics_loss.detach().float().mean().abs()
            d_finite = torch.isfinite(d_val)
            p_finite = torch.isfinite(p_val)
            both_finite = d_finite & p_finite

            if self._ema_data is None or self._ema_data.device != d_val.device:
                self._ema_data = torch.where(d_finite, d_val, torch.ones_like(d_val))
            else:
                self._ema_data = torch.where(
                    d_finite,
                    self.ema_decay * self._ema_data + (1.0 - self.ema_decay) * d_val,
                    self._ema_data,
                )

            p_nontrivial = p_finite & (p_val > self.eps)
            if self._ema_phys is None or self._ema_phys.device != p_val.device:
                self._ema_phys = torch.where(p_nontrivial, p_val, torch.zeros_like(p_val))
            else:
                updated_phys = torch.where(
                    self._ema_phys <= self.eps,
                    p_val,
                    self.ema_decay * self._ema_phys + (1.0 - self.ema_decay) * p_val,
                )
                self._ema_phys = torch.where(p_nontrivial, updated_phys, self._ema_phys)

            raw_ratio = self._ema_data / (self._ema_phys + self.eps)
            clamped_scale = torch.clamp(raw_ratio, min=self.min_scale, max=self.max_scale)
            scale = torch.where(
                self._ema_phys > self.eps,
                clamped_scale,
                torch.ones_like(clamped_scale),
            )
            eff_weight = (self.base_weight * warmup) * scale
            eff_weight = torch.where(both_finite, eff_weight, torch.zeros_like(eff_weight))

            self._last_scale = scale
            self._last_effective_weight = eff_weight

        safe_phys = torch.nan_to_num(physics_loss, nan=0.0, posinf=0.0, neginf=0.0)
        return eff_weight.to(dtype=safe_phys.dtype) * safe_phys

    def __call__(
        self,
        data_loss: torch.Tensor,
        physics_loss: Union[torch.Tensor, float, int],
    ) -> Union[torch.Tensor, float]:
        return self.balance(data_loss, physics_loss)


__all__ = ["AdaptivePhysicsLossBalancer"]
