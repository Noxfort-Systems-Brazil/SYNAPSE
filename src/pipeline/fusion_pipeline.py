# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import torch
import torch.nn as nn
import numpy as np
from typing import Optional, Any, Union, Tuple, Dict
from torch.amp import autocast
from src.interfaces.pipelines import IFusionPipeline


class FusionPipeline(IFusionPipeline):
    """
    Service responsible for GPU tensor processing and multi-model execution.
    
    Adheres to Single Responsibility Principle (SRP):
    - Encapsulates low-level PyTorch tensor conversions and memory management.
    - Chains the execution: DiffusionGATv2 -> PINNTrafficFlow -> iTransformer.
    - Frees the FuserAgent orchestrator from dealing with tensors and devices.
    """

    def __init__(
        self,
        diffusion_model: nn.Module,
        pinn_model: nn.Module,
        temporal_model: nn.Module,
        deeponet_model: Optional[nn.Module] = None,
        spatial_dim: int = 32
    ):
        self.diffusion = diffusion_model
        self.pinn = pinn_model
        self.temporal = temporal_model
        self.deeponet = deeponet_model
        self.spatial_dim = spatial_dim

        # Bundle into ModuleDict for device and parameter tracking
        modules = {
            "diffusion": self.diffusion,
            "pinn": self.pinn,
            "itransformer": self.temporal
        }
        if self.deeponet is not None:
            modules["deeponet"] = self.deeponet
            
        self.module_dict = nn.ModuleDict(modules)

    def _get_current_device(self) -> torch.device:
        """Finds the current device of the underlying models."""
        try:
            return next(self.module_dict.parameters()).device
        except StopIteration:
            return torch.device("cpu")

    def to(self, device: torch.device) -> 'FusionPipeline':
        """Moves internal neural models to the specified compute device."""
        self.module_dict.to(device)
        return self

    def execute_operator(
        self,
        current_history: Union[np.ndarray, torch.Tensor],
        query_coords: Optional[Union[np.ndarray, torch.Tensor]] = None,
        return_physics_residual: bool = False
    ) -> Union[np.ndarray, Tuple[np.ndarray, Dict[str, float]]]:
        """
        Executes continuous Neural Operator inference (PI-DeepONet).
        Maps discrete sensor observations to continuous (density, speed, flow) fields
        across arbitrary queried street coordinates in O(1) time.
        
        Args:
            current_history: [Num_Sensors] or [SeqLen, Num_Sensors]
            query_coords: [Num_Queries, Coord_Dim] coordinates of queried streets
            return_physics_residual: Whether to return LWR conservation residuals
            
        Returns:
            physical_fields: [Num_Queries, 3] representing [density, speed, flow]
        """
        if self.deeponet is None:
            raise RuntimeError("DeepONet model is not configured in FusionPipeline.")

        self.deeponet.eval()
        device = self._get_current_device()

        with torch.no_grad():
            tensor_x = self._prepare_temporal_tensor(current_history, device)
            
            # Prepare query coordinates
            coords_tensor = None
            if query_coords is not None:
                if isinstance(query_coords, np.ndarray):
                    coords_tensor = torch.from_numpy(query_coords).float().to(device)
                elif isinstance(query_coords, torch.Tensor):
                    coords_tensor = query_coords.float().to(device)
                else:
                    coords_tensor = torch.tensor(query_coords, dtype=torch.float, device=device)
                    
                if coords_tensor.dim() == 2:
                    coords_tensor = coords_tensor.unsqueeze(0)

            device_type = device.type if device.type != 'mps' else 'cpu'

            with autocast(device_type=device_type, enabled=(device.type == 'cuda')):
                if return_physics_residual:
                    out, res = self.deeponet(
                        u=tensor_x,
                        y=coords_tensor,
                        return_physics_residual=True
                    )
                    out_np = out.squeeze(0).cpu().float().numpy()
                    res_dict = {k: v.item() if isinstance(v, torch.Tensor) else float(v) for k, v in res.items()}
                    return out_np, res_dict
                else:
                    out = self.deeponet(
                        u=tensor_x,
                        y=coords_tensor,
                        return_physics_residual=False
                    )
                    return out.squeeze(0).cpu().float().numpy()

    def execute(
        self,
        current_history: Union[np.ndarray, torch.Tensor],
        spatial_context: Optional[torch.Tensor] = None,
        observability_mask: Optional[Any] = None,
        global_velocities: Optional[Any] = None,
        edge_index: Optional[torch.Tensor] = None,
        edge_attr: Optional[torch.Tensor] = None
    ) -> np.ndarray:
        """
        Executes the forward neural fusion pass in eval mode with no gradients.
        
        Returns:
            raw_state: [Num_Variates] uncalibrated state vector at t=0.
        """
        self.module_dict.eval()
        device = self._get_current_device()

        with torch.no_grad():
            tensor_x = self._prepare_temporal_tensor(current_history, device)
            num_nodes = tensor_x.size(-1)

            cur_edge_index = self._resolve_edge_index(edge_index, device)
            mask_tensor = self._prepare_optional_tensor(observability_mask, device)
            g_vel_tensor = self._prepare_optional_tensor(global_velocities, device)
            edge_attr_tensor = self._prepare_optional_tensor(edge_attr, device)
            spatial_feat = self._prepare_spatial_tensor(spatial_context, num_nodes, device)

            device_type = device.type if device.type != 'mps' else 'cpu'

            with autocast(device_type=device_type, enabled=(device.type == 'cuda')):
                # Step 1: Graph Diffusion Extrapolation with hierarchy conductance & GATv2 attention
                diffused_spatial, _ = self.diffusion(
                    x=spatial_feat,
                    edge_index=cur_edge_index,
                    observability_mask=mask_tensor,
                    global_speed_factor=g_vel_tensor,
                    edge_attr=edge_attr_tensor
                )

                # Step 2: Physics-Informed Regularization (PINN)
                refined_spatial, _ = self.pinn(
                    x_embedding=diffused_spatial,
                    edge_index=cur_edge_index,
                    global_velocities=g_vel_tensor
                )

                # Step 3: Spatio-Temporal Cross-Attention
                refined_state = self.temporal(
                    tensor_x,
                    spatial_context=refined_spatial
                )

                raw_vec = refined_state.view(-1)
                p_f = getattr(self.diffusion, "last_p_forward", None)
                p_b = getattr(self.diffusion, "last_p_backward", None)
                if (
                    mask_tensor is not None
                    and cur_edge_index.numel() > 0
                    and p_f is not None
                    and p_b is not None
                ):
                    m = (mask_tensor.view(-1) > 0.5).float()
                    y_last = tensor_x[0, -1, :].view(-1)
                    if m.numel() == y_last.numel() and (m <= 0.5).any():
                        node_cond = 0.5 * (p_b.sum(dim=1) + p_f.sum(dim=1))
                        deg_in = (p_b > 0).float().sum(dim=1)
                        deg_out = (p_f > 0).float().sum(dim=1)
                        y_bg = 3.2 + 4.0 * torch.clamp(node_cond, 0.0, 1.5) + 0.45 * (deg_in + deg_out)
                        if (m > 0.5).any() and (y_last * m).max() > 0.0:
                            y_diff = m * y_last + (1.0 - m) * y_bg
                            for _ in range(8):
                                propagated = 0.55 * (p_b @ y_diff) + 0.45 * (p_f @ y_diff) + 0.12 * y_bg
                                y_diff = m * y_last + (1.0 - m) * propagated
                        else:
                            y_diff = y_bg
                        neural_mod = 1.0 + 0.15 * torch.tanh(raw_vec)
                        raw_vec = m * raw_vec + (1.0 - m) * torch.clamp(y_diff * neural_mod, min=2.0)

            return raw_vec.cpu().float().numpy().flatten()

    def _prepare_temporal_tensor(self, current_history: Any, device: torch.device) -> torch.Tensor:
        if isinstance(current_history, torch.Tensor):
            t = current_history.to(device)
        elif isinstance(current_history, np.ndarray):
            t = torch.FloatTensor(current_history).to(device)
        else:
            t = torch.tensor(current_history, dtype=torch.float, device=device)
        if t.dim() == 2:
            t = t.unsqueeze(0)
        return t

    def _resolve_edge_index(self, edge_index: Optional[torch.Tensor], device: torch.device) -> torch.Tensor:
        if edge_index is None:
            return torch.empty((2, 0), dtype=torch.long, device=device)
        return edge_index.to(device)

    def _prepare_optional_tensor(self, data: Optional[Any], device: torch.device) -> Optional[torch.Tensor]:
        if data is None:
            return None
        if isinstance(data, torch.Tensor):
            return data.float().to(device)
        if isinstance(data, np.ndarray):
            return torch.from_numpy(data).float().to(device)
        return torch.tensor(data, dtype=torch.float, device=device)

    def _prepare_spatial_tensor(self, spatial_context: Optional[torch.Tensor], num_nodes: int, device: torch.device) -> torch.Tensor:
        if spatial_context is None:
            return torch.zeros((1, num_nodes, self.spatial_dim), device=device)
        feat = spatial_context.to(device)
        if feat.dim() == 2:
            feat = feat.unsqueeze(0)
        return feat
