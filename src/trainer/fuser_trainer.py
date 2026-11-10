# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from typing import Optional, Any
from torch.amp import autocast, GradScaler
from src.interfaces.trainers import IFuserTrainer
from src.physics.adaptive_loss_balancer import AdaptivePhysicsLossBalancer
from src.utils.convergence_tracker import MarginalConvergenceTracker
from src.utils.hardware import get_optimal_amp_dtype, requires_grad_scaler
from src.utils.logging_setup import get_logger

logger = get_logger("FuserTrainer")


class FuserTrainer(IFuserTrainer):
    """
    Dedicated training service for the Fuser neural pipeline.
    
    Adheres to Single Responsibility Principle (SRP):
    - Encapsulates optimizer, gradient scaling, and physics loss balancing.
    - Manages training loops, batch iterations, and early stopping convergence.
    """

    def __init__(
        self,
        composite_model: nn.Module,
        learning_rate: float = 0.0001,
        spatial_dim: int = 32,
        physics_weight: float = 0.05,
        optimizer: Optional[optim.Optimizer] = None,
        criterion: Optional[nn.Module] = None,
        adaptive_physics_balance: bool = True,
    ):
        self.model = composite_model
        self.spatial_dim = spatial_dim
        self.physics_weight = physics_weight
        self.adaptive_physics_balance = adaptive_physics_balance
        self.loss_balancer = AdaptivePhysicsLossBalancer(base_weight=physics_weight)
        
        self.optimizer = optimizer or optim.Adam(self.model.parameters(), lr=learning_rate)
        curr_device = self._get_current_device()
        self._amp_dtype = get_optimal_amp_dtype(curr_device)
        self.scaler = GradScaler(
            curr_device.type if curr_device.type in ('cuda', 'cpu') else 'cpu',
            enabled=requires_grad_scaler(curr_device, self._amp_dtype),
        )
        self.criterion = criterion or nn.MSELoss()

    def to(self, device: Any) -> 'FuserTrainer':
        """Transfers model and scaler to the target device."""
        target_device = torch.device(device) if isinstance(device, str) else device
        self.model.to(target_device)
        for state in self.optimizer.state.values():
            for k, v in state.items():
                if isinstance(v, torch.Tensor):
                    state[k] = v.to(target_device)
        self._amp_dtype = get_optimal_amp_dtype(target_device)
        self.scaler = GradScaler(
            target_device.type if target_device.type in ('cuda', 'cpu') else 'cpu',
            enabled=requires_grad_scaler(target_device, self._amp_dtype),
        )
        return self

    def _get_current_device(self) -> torch.device:
        """Introspects the model to find its actual physical device."""
        try:
            return next(self.model.parameters()).device
        except StopIteration:
            return torch.device("cpu")

    def _extract_spatial_context(self, inputs: torch.Tensor) -> torch.Tensor:
        """
        Builds a deterministic, parameter-free spatial feature tensor `[Batch, NumNodes, spatial_dim]`
        from temporal history `inputs` `[Batch, SeqLen, NumNodes]` so DiffusionGATv2 and
        PINOTrafficFlow1D receive real per-node state dynamics instead of all-zero tensors.
        """
        x_clean = torch.nan_to_num(inputs.float(), nan=0.0, posinf=0.0, neginf=0.0)
        batch_size, seq_len, num_nodes = x_clean.shape
        x_nodes = x_clean.transpose(1, 2).contiguous()  # [B, N, S]

        feat_mean = x_nodes.mean(dim=-1, keepdim=True)
        feat_std = x_nodes.std(dim=-1, unbiased=False, keepdim=True)
        feat_last = x_nodes[:, :, -1:]
        feat_trend = x_nodes[:, :, -1:] - x_nodes[:, :, :1]
        stats = torch.cat([feat_mean, feat_std, feat_last, feat_trend], dim=-1)

        if self.spatial_dim <= 4:
            return stats[..., :self.spatial_dim]

        rem = self.spatial_dim - 4
        flat_series = x_nodes.view(batch_size * num_nodes, 1, seq_len)
        if seq_len >= 2:
            profile = F.interpolate(flat_series, size=rem, mode="linear", align_corners=False)
        else:
            profile = F.interpolate(flat_series, size=rem, mode="nearest")
        profile = profile.view(batch_size, num_nodes, rem)
        return torch.cat([stats, profile], dim=-1)

    def train_step(self, batch_data: Any, cached_edge_index: Optional[torch.Tensor] = None) -> float:
        """
        Unified training step optimizing iTransformer, Diffusion, and PINN physics loss.
        """
        self.model.train()
        device = self._get_current_device()
        
        # Unpack inputs
        explicit_spatial = None
        if isinstance(batch_data, (tuple, list)):
            inputs = batch_data[0].to(device)
            targets = batch_data[1].to(device)
            edge_index = batch_data[2].to(device) if len(batch_data) > 2 and batch_data[2] is not None else cached_edge_index
            if len(batch_data) > 3 and batch_data[3] is not None:
                explicit_spatial = batch_data[3].to(device)
        else:
            inputs, targets = batch_data, batch_data
            inputs = inputs.to(device)
            targets = targets.to(device)
            edge_index = cached_edge_index
            
        if edge_index is None:
            edge_index = torch.empty((2, 0), dtype=torch.long, device=device)
        else:
            edge_index = edge_index.to(device)
            
        self.optimizer.zero_grad()
        device_type = device.type if device.type != 'mps' else 'cpu'
        amp_dtype = get_optimal_amp_dtype(device)
        
        diffusion = self.model["diffusion"] if isinstance(self.model, nn.ModuleDict) and "diffusion" in self.model else getattr(self.model, "diffusion", None)
        pinn = self.model["pinn"] if isinstance(self.model, nn.ModuleDict) and "pinn" in self.model else getattr(self.model, "pinn", None)
        itransformer = self.model["itransformer"] if isinstance(self.model, nn.ModuleDict) and "itransformer" in self.model else getattr(self.model, "itransformer", None)
        deeponet = self.model["deeponet"] if isinstance(self.model, nn.ModuleDict) and "deeponet" in self.model else getattr(self.model, "deeponet", None)

        spatial_ctx = None
        if diffusion is not None and pinn is not None:
            if explicit_spatial is not None:
                spatial_ctx = explicit_spatial
                if spatial_ctx.dim() == 2:
                    spatial_ctx = spatial_ctx.unsqueeze(0).expand(inputs.size(0), -1, -1)
            else:
                spatial_ctx = self._extract_spatial_context(inputs)

        with autocast(
            device_type=device_type,
            dtype=(amp_dtype if device.type == 'cuda' else torch.bfloat16),
            enabled=(device.type == 'cuda'),
        ):
            loss_physics = 0.0
            refined_spatial = None
            
            if diffusion is not None and pinn is not None and spatial_ctx is not None:
                diff_spatial, _ = diffusion(spatial_ctx, edge_index)
                refined_spatial, metrics = pinn(diff_spatial, edge_index)
                loss_physics = metrics.get("physics_residual", 0.0)
            
            # Forward through iTransformer
            if itransformer is not None:
                outputs = itransformer(inputs, spatial_context=refined_spatial)
            elif deeponet is not None:
                outputs = deeponet(inputs)
            else:
                raise RuntimeError("No temporal or operator model available in FuserTrainer.")
            
            # Shape alignment
            batch_size, pred_len, num_variates = outputs.shape
            if targets.dim() == 2: 
                targets = targets.view(batch_size, 1, num_variates)
            elif targets.dim() == 3 and targets.size(1) != pred_len:
                targets = targets[:, -pred_len:, :]
                
            loss_mse = self.criterion(outputs, targets)
            
            # DeepONet multi-task operator loss
            loss_deeponet = 0.0
            if deeponet is not None:
                _, deeponet_res = deeponet(inputs, return_physics_residual=True)
                loss_deeponet = deeponet_res.get("conservation_residual", 0.0)
            
            # Combined Loss (Data fidelity + Adaptive Physical consistency + DeepONet LWR residual)
            raw_physics = loss_physics + loss_deeponet
            weighted_physics = (
                self.loss_balancer(loss_mse, raw_physics)
                if self.adaptive_physics_balance
                else (self.physics_weight * raw_physics)
            )
            total_loss = loss_mse + weighted_physics

        self.scaler.scale(total_loss).backward()
        self.scaler.step(self.optimizer)
        self.scaler.update()
        
        return total_loss.item()

    def train(
        self,
        inputs: torch.Tensor,
        targets: torch.Tensor,
        epochs: int = 100,
        batch_size: int = 16,
        cached_edge_index: Optional[torch.Tensor] = None,
        tracker: Optional[MarginalConvergenceTracker] = None,
        use_dynamic_convergence: bool = True
    ) -> float:
        """
        Executes complete training epochs with dynamic convergence tracking.
        """
        dataset_size = inputs.size(0)
        
        if tracker is None and use_dynamic_convergence:
            tracker = MarginalConvergenceTracker(
                min_epochs=5,
                max_epochs=epochs,
                patience=4,
                min_delta=1e-4,
                restore_best_weights=True
            )

        max_loops = tracker.max_epochs if tracker else epochs
        target_model = self.model["itransformer"] if isinstance(self.model, nn.ModuleDict) and "itransformer" in self.model else self.model

        last_avg_loss = 0.0
        for epoch in range(max_loops):
            epoch_loss = 0.0
            permutation = torch.randperm(dataset_size)
            
            for i in range(0, dataset_size, batch_size):
                indices = permutation[i : i + batch_size]
                batch_x = inputs[indices]
                batch_y = targets[indices]
                
                loss = self.train_step((batch_x, batch_y), cached_edge_index=cached_edge_index)
                epoch_loss += loss
            
            avg_loss = epoch_loss / max(1, (dataset_size // batch_size))
            last_avg_loss = avg_loss
            
            if (epoch + 1) % 5 == 0 or epoch == 0:
                logger.info(f"Epoch [{epoch+1}] Total Loss: {avg_loss:.4f}")
            
            if tracker and tracker.step(epoch, avg_loss, model=target_model):
                logger.info(f"🛑 Converged at epoch {epoch+1} ({tracker.stop_reason}) | Best Loss: {tracker.best_loss:.4f}")
                break

        return last_avg_loss
