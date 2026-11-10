# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Optional, Dict, Any
import torch

from src.interfaces.physics import IFundamentalDiagram
from src.physics.fundamental_diagrams import GreenshieldsDiagram
from src.physics.continuum import SpatialGraphConservation


class PINOTrafficResidualEngine:
    """
    Physics-Informed Neural Operator (PINO) Residual Loss Engine.
    
    Encapsulates hydrodynamic conservation laws and constitutive relations:
    1. Constitutive diagram loss: |q - Q(k)|.
    2. Spatial Graph Conservation (Kirchhoff node divergence at junctions).
    3. Dynamic Continuity Equation (dk/dt + div(q) = 0).
    4. Corridor 1D LWR Conservation PDE (dk/dt + dq/dx = 0).
    """

    def __init__(
        self,
        fundamental_diagram: Optional[IFundamentalDiagram] = None,
        graph_conservation: Optional[SpatialGraphConservation] = None,
    ):
        self.fundamental_diagram = fundamental_diagram or GreenshieldsDiagram()
        self.graph_conservation = graph_conservation or SpatialGraphConservation()

    def compute_residuals(
        self,
        k_est: torch.Tensor,
        v_est: torch.Tensor,
        q_est: torch.Tensor,
        v_free: torch.Tensor,
        k_jam: torch.Tensor,
        edge_index: Optional[torch.Tensor] = None,
        operator_mode: str = "auto",
        dt: float = 1.0,
        dx: float = 1.0,
        k_next: Optional[torch.Tensor] = None,
        k_prev: Optional[torch.Tensor] = None,
        boundary_tolerance: Optional[float] = None,
        assume_stationary: bool = False,
    ) -> Dict[str, Any]:
        """
        Computes physical state projections, PDE residuals, and conservation metrics.
        
        Note on Corridor LWR PDE (dk/dt + dq/dx = 0):
            Transient continuity requires temporal reference states (`k_next` and/or `k_prev`).
            When neither is provided, `dk/dt` is NOT silently assumed to be zero unless
            `assume_stationary=True` is explicitly requested by the caller.
        
        Returns:
            Dictionary with density, speed, flow, and scalar/tensor loss residuals.
        """
        device = k_est.device
        num_nodes = k_est.shape[1]

        # 1. Constitutive relation: q = Q(k) (e.g. Greenshields)
        q_theory = self.fundamental_diagram.compute_flow(k_est, v_free, k_jam)
        res_constitutive = torch.abs(q_est - q_theory)

        is_graph = (edge_index is not None and edge_index.numel() > 0) or (operator_mode == "graph")
        temporal_continuity_active = False
        res_lwr_pde = torch.tensor(0.0, device=device)

        if is_graph:
            # Graph Mode: Spatial conservation across road junctions (Kirchhoff divergence)
            if edge_index is not None and edge_index.numel() > 0:
                res_conservation = self.graph_conservation.compute_loss(
                    q_est,
                    edge_index,
                    boundary_tolerance=boundary_tolerance
                )
            else:
                res_conservation = torch.tensor(0.0, device=device)

            # Dynamic continuity equation dk/dt + div(q) = 0 when temporal states are provided
            if (k_next is not None or k_prev is not None) and edge_index is not None and edge_index.numel() > 0:
                if k_next is not None and k_prev is not None:
                    k_target = k_next if k_next.dim() == 3 else k_next.unsqueeze(-1)
                    k_prior = k_prev if k_prev.dim() == 3 else k_prev.unsqueeze(-1)
                    dk_dt = (k_target - k_prior) / max(2.0 * dt, 1e-6)
                elif k_next is not None:
                    k_target = k_next if k_next.dim() == 3 else k_next.unsqueeze(-1)
                    dk_dt = (k_target - k_est) / max(dt, 1e-6)
                else:
                    k_prior = k_prev if k_prev.dim() == 3 else k_prev.unsqueeze(-1)
                    dk_dt = (k_est - k_prior) / max(dt, 1e-6)
                div_q = self.graph_conservation.compute_node_divergence(q_est, edge_index)
                res_continuity = torch.abs(dk_dt + div_q).mean()
                res_lwr_pde = res_continuity
                temporal_continuity_active = True
                physics_residual = res_constitutive.mean() + 0.1 * res_conservation + res_continuity
            else:
                physics_residual = res_constitutive.mean() + 0.1 * res_conservation
        else:
            # Corridor Mode: Real LWR conservation law: dk/dt + dq/dx = 0
            # Uses 2nd-order open-boundary finite differences (O(dx^2), free of periodic FFT Gibbs artifacts)
            res_conservation = torch.tensor(0.0, device=device)
            if num_nodes >= 3:
                inv_2dx = 1.0 / max(2.0 * dx, 1e-6)
                dq_left = (-3.0 * q_est[:, 0:1, :] + 4.0 * q_est[:, 1:2, :] - q_est[:, 2:3, :]) * inv_2dx
                dq_mid = (q_est[:, 2:, :] - q_est[:, :-2, :]) * inv_2dx
                dq_right = (3.0 * q_est[:, -1:, :] - 4.0 * q_est[:, -2:-1, :] + q_est[:, -3:-2, :]) * inv_2dx
                dq_dx = torch.cat([dq_left, dq_mid, dq_right], dim=1)

                if k_next is not None and k_prev is not None:
                    k_target = k_next if k_next.dim() == 3 else k_next.unsqueeze(-1)
                    k_prior = k_prev if k_prev.dim() == 3 else k_prev.unsqueeze(-1)
                    dk_dt = (k_target - k_prior) / max(2.0 * dt, 1e-6)
                    res_lwr_pde = torch.abs(dk_dt + dq_dx).mean()
                    temporal_continuity_active = True
                elif k_next is not None:
                    k_target = k_next if k_next.dim() == 3 else k_next.unsqueeze(-1)
                    dk_dt = (k_target - k_est) / max(dt, 1e-6)
                    res_lwr_pde = torch.abs(dk_dt + dq_dx).mean()
                    temporal_continuity_active = True
                elif k_prev is not None:
                    k_prior = k_prev if k_prev.dim() == 3 else k_prev.unsqueeze(-1)
                    dk_dt = (k_est - k_prior) / max(dt, 1e-6)
                    res_lwr_pde = torch.abs(dk_dt + dq_dx).mean()
                    temporal_continuity_active = True
                elif assume_stationary:
                    res_lwr_pde = torch.abs(dq_dx).mean()
                    temporal_continuity_active = True
            elif num_nodes == 2:
                dq_dx = (q_est[:, 1:, :] - q_est[:, :-1, :]) / max(dx, 1e-6)
                if k_next is not None and k_prev is not None:
                    k_target = k_next if k_next.dim() == 3 else k_next.unsqueeze(-1)
                    k_prior = k_prev if k_prev.dim() == 3 else k_prev.unsqueeze(-1)
                    dk_dt = (k_target[:, :-1, :] - k_prior[:, :-1, :]) / max(2.0 * dt, 1e-6)
                    res_lwr_pde = torch.abs(dk_dt + dq_dx).mean()
                    temporal_continuity_active = True
                elif k_next is not None:
                    k_target = k_next if k_next.dim() == 3 else k_next.unsqueeze(-1)
                    dk_dt = (k_target[:, :-1, :] - k_est[:, :-1, :]) / max(dt, 1e-6)
                    res_lwr_pde = torch.abs(dk_dt + dq_dx).mean()
                    temporal_continuity_active = True
                elif k_prev is not None:
                    k_prior = k_prev if k_prev.dim() == 3 else k_prev.unsqueeze(-1)
                    dk_dt = (k_est[:, :-1, :] - k_prior[:, :-1, :]) / max(dt, 1e-6)
                    res_lwr_pde = torch.abs(dk_dt + dq_dx).mean()
                    temporal_continuity_active = True
                elif assume_stationary:
                    res_lwr_pde = torch.abs(dq_dx).mean()
                    temporal_continuity_active = True

            physics_residual = res_constitutive.mean() + res_lwr_pde

        return {
            "density": k_est.squeeze(-1),
            "speed": v_est.squeeze(-1),
            "flow": q_est.squeeze(-1),
            "physics_residual": physics_residual,
            "res_flow": res_constitutive.mean(),
            "res_conservation": res_conservation,
            "res_lwr_pde": res_lwr_pde,
            "temporal_continuity_active": temporal_continuity_active,
        }


__all__ = ["PINOTrafficResidualEngine"]
