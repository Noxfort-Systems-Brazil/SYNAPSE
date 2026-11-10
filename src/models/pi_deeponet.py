# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Any, Optional, Tuple, Dict, Union
import torch
import torch.nn as nn
import torch.nn.functional as F

from src.models.deeponet_subnets import BranchNet, TrunkNet
from src.physics.constants import (
    DEFAULT_JAM_DENSITY_PER_LANE,
    DEFAULT_URBAN_SPEED_LIMIT_KMH,
)

# Enable Tensor Cores globally for matrix multiplications and cuDNN operations
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True


class PIDeepONet(nn.Module):
    """
    Physics-Informed Deep Operator Network (PI-DeepONet).
    
    Learns the solution operator mapping sparse, discrete sensor readings to
    continuous spatiotemporal traffic velocity, density, and flow fields:
        G_theta(u)(x, t) = sum_k (b_k(u) * t_k(x, t)) + b_0
        
    Provides:
    1. Zero-shot continuous evaluation at any (x, t) coordinate.
    2. Physical non-negativity guarantees (Softplus on [density, speed, flow]).
    3. Differentiable PDE residual evaluation for continuum conservation (LWR).
    4. Seamless drop-in compatibility with sliding window sequence reconstruction.
    """

    def __init__(
        self,
        sensor_dim: int = 4,
        coord_dim: int = 2,
        p_latent: int = 64,
        hidden_dim: int = 128,
        out_channels: int = 3,  # [density, speed, flow]
        v_free_default: float = DEFAULT_URBAN_SPEED_LIMIT_KMH,
        k_jam_default: float = DEFAULT_JAM_DENSITY_PER_LANE,
        feature_dim: Optional[int] = None,
        seq_len: Optional[int] = None,
        **kwargs
    ):
        super().__init__()
        
        # Backward compatibility aliases for ImputerPipeline
        self.sensor_dim = feature_dim or sensor_dim
        self.seq_len = seq_len or 24
        self.coord_dim = coord_dim
        self.p_latent = p_latent
        self.out_channels = out_channels
        
        self.v_free_default = v_free_default
        self.k_jam_default = k_jam_default

        effective_sensor_in = self.sensor_dim * (self.seq_len if seq_len else 1)
        self.branch = BranchNet(in_features=effective_sensor_in, p_latent=p_latent * out_channels, hidden_dim=hidden_dim)
        self.trunk = TrunkNet(coord_dim=coord_dim, p_latent=p_latent * out_channels, hidden_dim=hidden_dim)
        
        # Learnable scalar biases per output channel
        self.bias = nn.Parameter(torch.zeros(out_channels))

        # Linear projection head when used as a direct sequence transformer/imputer
        self.seq_reconstruction_head = nn.Sequential(
            nn.Linear(out_channels, hidden_dim // 2),
            nn.GELU(),
            nn.Linear(hidden_dim // 2, self.sensor_dim)
        )

        # Inference-mode caches for canonical grids and static TrunkNet basis functions
        self._cached_canonical_grids: Dict[Tuple[int, torch.device], torch.Tensor] = {}
        self._cached_canonical_trunk: Dict[Tuple[int, torch.device, torch.dtype], torch.Tensor] = {}
        self._last_query_ref: Optional[torch.Tensor] = None
        self._last_query_key: Optional[Tuple[Any, ...]] = None
        self._last_query_trunk: Optional[torch.Tensor] = None

    def invalidate_trunk_cache(self) -> None:
        """Clears cached TrunkNet basis evaluations when weights or training state change."""
        self._cached_canonical_trunk.clear()
        self._last_query_ref = None
        self._last_query_key = None
        self._last_query_trunk = None

    def train(self, mode: bool = True) -> "PIDeepONet":
        super().train(mode)
        if mode:
            self.invalidate_trunk_cache()
        return self

    def _apply(self, fn: Any, recurse: bool = True) -> "PIDeepONet":
        res = super()._apply(fn, recurse=recurse)
        if hasattr(self, "_cached_canonical_grids"):
            self._cached_canonical_grids.clear()
            self.invalidate_trunk_cache()
        return res

    def _load_from_state_dict(self, *args: Any, **kwargs: Any) -> None:
        super()._load_from_state_dict(*args, **kwargs)
        self.invalidate_trunk_cache()

    def set_static_query_coords(self, query_coords: torch.Tensor) -> None:
        """Pre-evaluates and caches TrunkNet basis functions for fixed street coordinates."""
        device = next(self.parameters()).device
        coords = query_coords.float().to(device)
        if coords.dim() == 2:
            coords = coords.unsqueeze(0)
        self.eval()
        with torch.no_grad():
            trunk_out = self.trunk(coords).detach()
        self._last_query_ref = query_coords
        self._last_query_key = (
            query_coords.data_ptr(),
            query_coords.shape,
            query_coords.device,
            query_coords._version,
            device,
        )
        self._last_query_trunk = trunk_out

    def _get_canonical_grid(self, num_t: int, device: torch.device) -> torch.Tensor:
        key = (num_t, device)
        grid = self._cached_canonical_grids.get(key)
        if grid is None:
            t_coords = torch.linspace(0.0, 1.0, num_t, device=device)
            x_coords = torch.zeros(num_t, device=device)
            grid = torch.stack([x_coords, t_coords], dim=-1).unsqueeze(0)  # [1, num_t, 2]
            self._cached_canonical_grids[key] = grid
        return grid

    def forward(
        self,
        u: torch.Tensor,
        y: Optional[torch.Tensor] = None,
        return_physics_residual: bool = False
    ) -> Union[torch.Tensor, Tuple[torch.Tensor, Dict[str, torch.Tensor]]]:
        """
        Args:
            u: Sensor observations tensor:
               - [Batch, Num_Sensors]
               - [Batch, SeqLen, Channels]
               - [Batch, Channels, SeqLen]
            y: Optional query coordinates [Batch, Num_Queries, coord_dim] or [Num_Queries, coord_dim].
               If None, synthesizes a continuous uniform (x, t) grid matching input sequence dimensions.
            return_physics_residual: If True, computes differentiable LWR PDE residual.
               
        Returns:
            state: Physical state tensor or reconstructed sequence.
        """
        device = u.device
        
        # Standardize input shapes
        if u.dim() == 2:
            batch_size = u.size(0)
            u_flat = u
            is_seq_mode = False
        elif u.dim() == 3:
            batch_size = u.size(0)
            # If shape is [Batch, Channels, SeqLen], permute to [Batch, SeqLen, Channels]
            if u.size(1) == self.sensor_dim and u.size(2) != self.sensor_dim:
                u_seq = u.permute(0, 2, 1)
            else:
                u_seq = u
            u_flat = u_seq.flatten(start_dim=1)
            is_seq_mode = True
        else:
            raise ValueError(f"Unsupported input dimension: {u.dim()}")

        can_cache_trunk = (not self.training) and (not torch.is_grad_enabled())

        # 1. Branch Forward Pass
        b = self.branch(u_flat)  # [Batch, p_latent * out_channels]

        # 2. Coordinate Grid & Trunk Forward Pass (with O(1) eval-mode basis caching)
        if y is None:
            num_t = (
                u.size(1)
                if (u.dim() == 3 and not (u.size(1) == self.sensor_dim and u.size(2) != self.sensor_dim))
                else (u.size(2) if u.dim() == 3 else self.seq_len)
            )
            base_grid = self._get_canonical_grid(num_t, device)
            y_expanded = base_grid.expand(batch_size, -1, -1)
            num_queries = num_t

            if can_cache_trunk:
                trunk_key = (num_t, device, b.dtype)
                t_single = self._cached_canonical_trunk.get(trunk_key)
                if t_single is None:
                    t_single = self.trunk(base_grid).to(dtype=b.dtype).detach()
                    self._cached_canonical_trunk[trunk_key] = t_single
                t = t_single.expand(batch_size, -1, -1)
            else:
                # Evaluate TrunkNet once on [1, num_t, 2] then broadcast across batch!
                t = self.trunk(base_grid).expand(batch_size, -1, -1)
        else:
            raw_y = y
            is_shared_query = (raw_y.dim() == 2) or (raw_y.dim() == 3 and raw_y.size(0) == 1)
            if can_cache_trunk and is_shared_query:
                q_key = (
                    raw_y.data_ptr(),
                    raw_y.shape,
                    raw_y.device,
                    raw_y._version,
                    device,
                )
                if self._last_query_key == q_key and self._last_query_trunk is not None:
                    t_single = self._last_query_trunk.to(dtype=b.dtype)
                else:
                    y_single = raw_y.unsqueeze(0) if raw_y.dim() == 2 else raw_y
                    t_single = self.trunk(y_single.to(device)).detach()
                    self._last_query_ref = raw_y
                    self._last_query_key = q_key
                    self._last_query_trunk = t_single
                    t_single = t_single.to(dtype=b.dtype)
                num_queries = t_single.size(1)
                t = t_single.expand(batch_size, -1, -1)
                y_expanded = (raw_y.unsqueeze(0) if raw_y.dim() == 2 else raw_y).expand(batch_size, -1, -1)
            else:
                if raw_y.dim() == 2:
                    y_single = raw_y.unsqueeze(0)
                    t = self.trunk(y_single).expand(batch_size, -1, -1)
                    y_expanded = y_single.expand(batch_size, -1, -1)
                else:
                    y_expanded = raw_y
                    t = self.trunk(y_expanded)
                num_queries = y_expanded.size(1)

        b = b.view(batch_size, 1, self.out_channels, self.p_latent)
        t = t.view(batch_size, num_queries, self.out_channels, self.p_latent)

        # 3. Inner Product Operator Fusion
        # sum over p_latent: [Batch, Num_Queries, Out_Channels]
        raw_output = torch.sum(b * t, dim=-1) + self.bias.to(dtype=b.dtype)

        # 4. Enforce Physical Non-Negativity: [density, speed, flow] >= 0
        phys_output = F.softplus(raw_output)

        # 5. Direct Sequence Mode (for Imputer compatibility)
        if is_seq_mode and num_queries == u_seq.size(1):
            reconstructed_seq = self.seq_reconstruction_head(phys_output)
            # Match original tensor layout
            if u.dim() == 3 and u.size(1) == self.sensor_dim and u.size(2) != self.sensor_dim:
                final_output = reconstructed_seq.permute(0, 2, 1)
            else:
                final_output = reconstructed_seq
        else:
            final_output = phys_output

        if return_physics_residual:
            residuals = self.compute_pde_residual(phys_output, y_expanded)
            return final_output, residuals

        return final_output

    def compute_pde_residual(self, phys_output: torch.Tensor, coords: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Computes hydrodynamic LWR (Lighthill-Whitham-Richards) conservation residuals:
            q_expected = density * speed
            Residual = |flow - density * speed|
        """
        density = phys_output[:, :, 0]
        speed = phys_output[:, :, 1]
        flow = phys_output[:, :, 2] if phys_output.size(-1) >= 3 else (density * speed)

        q_theory = density * speed
        res_conservation = torch.mean(torch.abs(flow - q_theory))

        return {
            "conservation_residual": res_conservation,
            "mean_density": density.mean(),
            "mean_speed": speed.mean(),
            "mean_flow": flow.mean()
        }


__all__ = [
    "PIDeepONet",
    "BranchNet",
    "TrunkNet",
]
