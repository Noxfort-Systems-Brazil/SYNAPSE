# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Optional, Dict, Tuple, Union, Any
import torch
import torch.nn as nn
import torch.nn.functional as F

from src.interfaces.physics import IFundamentalDiagram
from src.physics.fundamental_diagrams import GreenshieldsDiagram
from src.physics.continuum import SpatialGraphConservation
from src.physics.pino_residuals import PINOTrafficResidualEngine
from src.blocks.spectral_blocks import SpectralConv1d, SpectralConv2d, GraphLaplacianSpectralConv
from src.blocks.feature_blocks import SpectralFeatureBlock, SpectralFeatureExtractor
from src.physics.constants import (
    DEFAULT_JAM_DENSITY_PER_LANE,
    DEFAULT_URBAN_SPEED_LIMIT_KMH,
)


class PINOTrafficFlow1D(nn.Module):
    """
    Physics-Informed Neural Operator (PINO) for Macroscopic Traffic Flow.
    
    Combines:
    1. Fourier Neural Operator (FNO) Spectral Convolutions for fast continuous simulation.
    2. Hydrodynamic Lighthill-Whitham-Richards (LWR) PDE residual constraints.
    3. Pluggable integration with FusionPipeline and spatial road graphs.
    """

    def __init__(
        self,
        in_channels: int = 32,
        hidden_dim: int = 64,
        modes: int = 16,
        num_layers: int = 4,
        v_free_default: float = DEFAULT_URBAN_SPEED_LIMIT_KMH,
        k_jam_default: float = DEFAULT_JAM_DENSITY_PER_LANE,
        q_max_default: float = 1800.0,
        fundamental_diagram: Optional[IFundamentalDiagram] = None,
        graph_conservation: Optional[SpatialGraphConservation] = None,
        residual_engine: Optional[PINOTrafficResidualEngine] = None,
        operator_mode: str = "auto",
        cheb_k: int = 3,
        **kwargs
    ):
        super().__init__()
        self.in_channels = in_channels
        self.hidden_dim = hidden_dim
        self.modes = modes
        self.num_layers = num_layers
        self.operator_mode = operator_mode
        self.cheb_k = cheb_k

        self.v_free_default = v_free_default
        self.k_jam_default = k_jam_default
        self.q_max_default = q_max_default

        self.fundamental_diagram = fundamental_diagram or GreenshieldsDiagram()
        self.graph_conservation = graph_conservation or SpatialGraphConservation()
        self.residual_engine = residual_engine or PINOTrafficResidualEngine(
            fundamental_diagram=self.fundamental_diagram,
            graph_conservation=self.graph_conservation,
        )

        # 1. Lifting projection: In -> Hidden Width
        self.p_lifting = nn.Linear(in_channels, hidden_dim)

        # 2. Fourier Neural Operator Blocks (for 1D ordered corridor cells)
        self.spectral_layers = nn.ModuleList([
            SpectralConv1d(hidden_dim, hidden_dim, modes) for _ in range(num_layers)
        ])
        # Graph Laplacian Spectral Blocks (permutation-equivariant for road graphs)
        self.graph_spectral_layers = nn.ModuleList([
            GraphLaplacianSpectralConv(hidden_dim, hidden_dim, K=cheb_k) for _ in range(num_layers)
        ])
        self.w_layers = nn.ModuleList([
            nn.Conv1d(hidden_dim, hidden_dim, 1) for _ in range(num_layers)
        ])

        # 3. Projection Head: Hidden Width -> Physical States [density, speed, flow]
        self.physical_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.GELU(),
            nn.Linear(hidden_dim // 2, 3)
        )

        # 4. Latent Physics Gate: Refines embedding with physical states
        self.physics_gate = nn.Sequential(
            nn.Linear(in_channels + 3, in_channels),
            nn.Sigmoid()
        )

        # 5. Parameter adapter for local road variation
        self.param_adapter = nn.Sequential(
            nn.Linear(in_channels, 2),
            nn.Tanh()
        )
        self._cached_lap_key: Optional[Tuple[Any, ...]] = None
        self._cached_sparse_lap: Optional[Tuple[torch.Tensor, torch.Tensor, torch.Tensor]] = None

    def _get_or_compute_sparse_laplacian(
        self,
        num_nodes: int,
        edge_index: Optional[torch.Tensor],
        device: torch.device,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        if edge_index is None or edge_index.numel() == 0:
            empty_i = torch.empty(0, dtype=torch.long, device=device)
            empty_w = torch.empty(0, dtype=torch.float32, device=device)
            return empty_i, empty_i, empty_w

        if not self.training and not torch.is_grad_enabled():
            cache_key = (
                num_nodes,
                device,
                edge_index.data_ptr(),
                edge_index.shape,
                edge_index._version,
            )
            if self._cached_lap_key == cache_key and self._cached_sparse_lap is not None:
                return self._cached_sparse_lap
            sparse_lap = GraphLaplacianSpectralConv.compute_sparse_laplacian_edges(
                num_nodes=num_nodes,
                edge_index=edge_index,
                device=device,
            )
            self._cached_lap_key = cache_key
            self._cached_sparse_lap = sparse_lap
            return sparse_lap

        return GraphLaplacianSpectralConv.compute_sparse_laplacian_edges(
            num_nodes=num_nodes,
            edge_index=edge_index,
            device=device,
        )

    def forward_operator(
        self,
        x: torch.Tensor,
        edge_index: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Spectral operator forward pass.
        - In graph mode (or auto when edge_index is provided): uses Graph Laplacian
          spectral convolutions, preserving physical topology and permutation equivariance.
        - In corridor mode (or auto when edge_index is None): uses 1D FFT convolutions
          along spatially ordered cells of a roadway corridor.
        
        Args:
            x: [Batch, Num_Nodes, in_channels]
            edge_index: Optional [2, Num_Edges] connectivity
        Returns:
            x_latent: [Batch, Num_Nodes, hidden_dim]
        """
        use_graph = (self.operator_mode == "graph") or (
            self.operator_mode == "auto" and edge_index is not None and edge_index.numel() > 0
        )

        if use_graph:
            # Graph Laplacian spectral operator (shared O(|E|) sparse Laplacian across all layers)
            x_lifted = self.p_lifting(x)
            sparse_lap = self._get_or_compute_sparse_laplacian(
                num_nodes=x_lifted.size(1),
                edge_index=edge_index,
                device=x_lifted.device,
            )
            for graph_conv, w_conv in zip(self.graph_spectral_layers, self.w_layers):
                x1 = graph_conv(x_lifted, sparse_laplacian=sparse_lap)
                x2 = w_conv(x_lifted.permute(0, 2, 1)).permute(0, 2, 1)
                x_lifted = F.gelu(x1 + x2)
            return x_lifted
        else:
            # 1D Corridor spectral operator along ordered cells
            x_lifted = self.p_lifting(x).permute(0, 2, 1)
            for spec_conv, w_conv in zip(self.spectral_layers, self.w_layers):
                x1 = spec_conv(x_lifted)
                x2 = w_conv(x_lifted)
                x_lifted = F.gelu(x1 + x2)
            return x_lifted.permute(0, 2, 1)

    def project_physical_states(self, x_latent: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Projects latent operator representations to non-negative [k, v, q].
        """
        raw_physics = self.physical_head(x_latent)
        k_est = F.softplus(raw_physics[:, :, 0:1])
        v_est = F.softplus(raw_physics[:, :, 1:2])
        q_est = F.softplus(raw_physics[:, :, 2:3])
        return k_est, v_est, q_est

    def forward(
        self,
        x_embedding: torch.Tensor,
        edge_index: Optional[torch.Tensor] = None,
        global_velocities: Optional[torch.Tensor] = None,
        dt: float = 1.0,
        dx: float = 1.0,
        k_next: Optional[torch.Tensor] = None,
        k_prev: Optional[torch.Tensor] = None,
        boundary_tolerance: Optional[float] = None,
        assume_stationary: bool = False,
    ) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Compatible with FusionPipeline:
        Args:
            x_embedding: [Batch, Num_Nodes, in_channels] or [Num_Nodes, in_channels]
            edge_index: Graph connectivity [2, Num_Edges]
            global_velocities: Optional macroscopic speeds
            dt: Time differential
            dx: Spatial differential for corridor discretization
            k_next: Optional next-timestep density [Batch, Num_Nodes, 1]
            k_prev: Optional previous-timestep density [Batch, Num_Nodes, 1]
            boundary_tolerance: Optional tolerance for boundary Kirchhoff imbalances
            assume_stationary: Explicit flag to enforce dk/dt = 0 when k_next/k_prev are absent
        Returns:
            refined_embedding: [Batch, Num_Nodes, in_channels]
            metrics: Dictionary containing physical variables and PDE residuals
        """
        if x_embedding.dim() == 2:
            x_embedding = x_embedding.unsqueeze(0)

        batch_size, num_nodes, _ = x_embedding.shape
        device = x_embedding.device

        # 1. Neural Operator Pass
        x_latent = self.forward_operator(x_embedding, edge_index=edge_index)

        # 2. Physical State Projections
        k_est, v_est, q_est = self.project_physical_states(x_latent)

        # 3. Learnable road parameter offsets
        offsets = self.param_adapter(x_embedding)
        v_free = self.v_free_default * (1.0 + 0.2 * offsets[:, :, 0:1])
        k_jam = self.k_jam_default * (1.0 + 0.2 * offsets[:, :, 1:2])

        # 4. Macro velocity boundary constraint
        if global_velocities is not None:
            g_vel = global_velocities.to(device)
            if g_vel.dim() == 1:
                g_vel = g_vel.unsqueeze(0).unsqueeze(-1).expand(batch_size, num_nodes, 1)
            elif g_vel.dim() == 2 and g_vel.shape[-1] != 1:
                g_vel = g_vel.unsqueeze(-1)
            valid_mask = (g_vel > 0).float()
            v_est = v_est * (1.0 - 0.5 * valid_mask) + g_vel * (0.5 * valid_mask)

        # 5. Hydrodynamic LWR Conservation PDE & Constitutive Residual (Delegated Engine)
        metrics = self.residual_engine.compute_residuals(
            k_est=k_est,
            v_est=v_est,
            q_est=q_est,
            v_free=v_free,
            k_jam=k_jam,
            edge_index=edge_index,
            operator_mode=self.operator_mode,
            dt=dt,
            dx=dx,
            k_next=k_next,
            k_prev=k_prev,
            boundary_tolerance=boundary_tolerance,
            assume_stationary=assume_stationary,
        )

        # 6. Latent Gate Injection
        physics_vector = torch.cat([k_est, v_est, q_est], dim=-1)
        gate_input = torch.cat([x_embedding, physics_vector], dim=-1)
        gate = self.physics_gate(gate_input)

        refined_embedding = x_embedding * gate

        return refined_embedding, metrics


__all__ = [
    "PINOTrafficFlow1D",
    "SpectralFeatureBlock",
    "SpectralFeatureExtractor",
]
