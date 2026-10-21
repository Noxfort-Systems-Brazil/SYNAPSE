# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Protocol, runtime_checkable, Dict, Optional, Union
import torch


@runtime_checkable
class IFundamentalDiagram(Protocol):
    """
    Contract for macroscopic traffic fundamental diagrams (Relation between density k, speed v, and flow q).
    """
    def compute_flow(
        self,
        density: torch.Tensor,
        v_free: torch.Tensor,
        k_jam: torch.Tensor
    ) -> torch.Tensor:
        """Computes theoretical macroscopic traffic flow q given density, free-flow speed, and jam density."""
        ...

    def compute_speed(
        self,
        density: torch.Tensor,
        v_free: torch.Tensor,
        k_jam: torch.Tensor
    ) -> torch.Tensor:
        """Computes theoretical macroscopic speed v given density, free-flow speed, and jam density."""
        ...


@runtime_checkable
class IPhysicsConstraint(Protocol):
    """
    Contract for individual differentiable traffic physics constraints/invariants (PINN).
    """
    def compute_residual(self, state: torch.Tensor, **kwargs) -> torch.Tensor:
        """Computes penalty or residual loss term for the given state tensor."""
        ...


@runtime_checkable
class IPhysicsLossEngine(Protocol):
    """
    Contract for the PINN physics loss aggregation engine.
    """
    def compute_losses(
        self,
        reconstruction: torch.Tensor,
        orig_x: Optional[torch.Tensor] = None,
        edge_index: Optional[torch.Tensor] = None,
        **kwargs
    ) -> Dict[str, torch.Tensor]:
        """
        Computes all physics loss components (bounds, kinematics, smoothness, conservation)
        and returns a dictionary containing individual terms and 'total_physics_loss'.
        """
        ...


__all__ = [
    "IFundamentalDiagram",
    "IPhysicsConstraint",
    "IPhysicsLossEngine"
]
