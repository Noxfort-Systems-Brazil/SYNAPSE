# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
from typing import Tuple, Dict, Optional, Any, Union
import torch
import torch.nn as nn
from transformers import AutoModel, AutoConfig

from src.utils.model_paths import get_modernbert_path

# Enable Tensor Cores globally for matrix multiplications and cuDNN operations
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True


class TCNAE(nn.Module):
    """
    Temporal Convolutional Autoencoder with Physics Projection Head.
    Operates purely on spatial/semantic embedding channels over time.
    Decoupled from Transformer backbone for fast Optuna HPO tuning.
    """
    def __init__(self, hidden_size: int = 768, latent_dim: int = 64, kernel_size: int = 3):
        super(TCNAE, self).__init__()
        self.hidden_size = hidden_size
        self.latent_dim = latent_dim
        self.kernel_size = kernel_size
        padding = kernel_size // 2

        # 1. Neural Reasoner (TCN Autoencoder Encoder)
        self.encoder = nn.Sequential(
            nn.Conv1d(in_channels=self.hidden_size, out_channels=256, kernel_size=kernel_size, padding=padding),
            nn.ReLU(),
            nn.BatchNorm1d(256),
            nn.Conv1d(in_channels=256, out_channels=latent_dim, kernel_size=kernel_size, padding=padding),
            nn.ReLU()
        )
        
        # 2. Physics Head: Latent Space -> Physical State Projections [q (flow), v (speed), rho (density)]
        self.physics_head = nn.Sequential(
            nn.Conv1d(in_channels=latent_dim, out_channels=64, kernel_size=1),
            nn.ReLU(),
            nn.Conv1d(in_channels=64, out_channels=3, kernel_size=1)
        )
        
        # 3. Decoder: Reconstruct original semantic embeddings
        self.decoder = nn.Sequential(
            nn.Conv1d(in_channels=latent_dim, out_channels=256, kernel_size=kernel_size, padding=padding),
            nn.ReLU(),
            nn.BatchNorm1d(256),
            nn.Conv1d(in_channels=256, out_channels=self.hidden_size, kernel_size=kernel_size, padding=padding)
        )
        
        # Module Dict grouping for backward compatibility
        self.ae = nn.ModuleDict({
            "encoder": self.encoder,
            "physics_head": self.physics_head,
            "decoder": self.decoder
        })

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Args:
            x: Tensor [Batch, HiddenSize, SeqLen]
        Returns:
            reconstructed_x: [Batch, HiddenSize, SeqLen]
            latent: [Batch, LatentDim, SeqLen]
            physics_states: [Batch, 3, SeqLen]
        """
        latent = self.encoder(x)
        physics_states = self.physics_head(latent)
        reconstructed_x = self.decoder(latent)
        return reconstructed_x, latent, physics_states


class NeuroSymbolicModel(nn.Module):
    """
    Pure Neuro-Symbolic Neural Architecture for the Linguist Agent.
    
    Architecture:
    1. Semantic Backbone: Transformer (ModernBERT) - Extracts language representations.
    2. Neural Reasoner: TCN Autoencoder compressing into bottleneck manifold.
    3. Physics Projection Head: Latent Space -> Physical State Projections [q (flow), v (speed), rho (density)].
    4. Semantic Decoder: Reconstructs original semantic embeddings.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        freeze_transformer: bool = True,
        latent_dim: int = 64,
        kernel_size: int = 3,
        transformer: Optional[nn.Module] = None,
        physics_loss_engine: Optional[Any] = None
    ):
        super(NeuroSymbolicModel, self).__init__()
        resolved_name = model_name or get_modernbert_path()
        self.model_name = resolved_name
        self.latent_dim = latent_dim
        self.kernel_size = kernel_size
        
        # 1. Semantic Backbone (Transformer - DIP support)
        if transformer is not None:
            self.transformer = transformer
            self.hidden_size = getattr(transformer.config, "hidden_size", 768)
        else:
            is_local = os.path.isdir(resolved_name)
            self.config = AutoConfig.from_pretrained(resolved_name, local_files_only=is_local)
            self.hidden_size = self.config.hidden_size
            self.transformer = AutoModel.from_pretrained(resolved_name, local_files_only=is_local)
        
        self.freeze_transformer = freeze_transformer
        if freeze_transformer:
            for param in self.transformer.parameters():
                param.requires_grad = False
            self.transformer.eval()
            self.transformer.training = False
                
        # Optional Physics Engine reference for backward compatibility
        self.physics_engine = physics_loss_engine

        # 2. Neural Reasoner & Physics Head (Decoupled TCNAE)
        self.tcnae = TCNAE(
            hidden_size=self.hidden_size,
            latent_dim=latent_dim,
            kernel_size=kernel_size
        )
        self.encoder = self.tcnae.encoder
        self.physics_head = self.tcnae.physics_head
        self.decoder = self.tcnae.decoder
        self.ae = self.tcnae.ae

    def train(self, mode: bool = True) -> "NeuroSymbolicModel":
        """Sets training mode while keeping the Transformer backbone frozen in eval mode if freeze_transformer=True."""
        super().train(mode)
        if self.freeze_transformer:
            self.transformer.eval()
            self.transformer.training = False
        else:
            self.transformer.training = bool(mode)
        return self

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        return_physics_residuals: bool = True,
        semantic_type: Optional[str] = None,
        **kwargs
    ) -> Union[Tuple[torch.Tensor, torch.Tensor, torch.Tensor], Tuple[torch.Tensor, torch.Tensor, Dict[str, torch.Tensor]]]:
        """
        Forward pass through Transformer -> TCN Reasoner -> Physics Projection.
        
        Returns:
            reconstruction: Reconstructed semantic embeddings [Batch, SeqLen, HiddenDim]
            original_embeddings: Raw transformer embeddings [Batch, SeqLen, HiddenDim]
            physics_output: Projected states tensor or physical residuals dictionary
        """
        # 1. Get Semantic Embeddings (enable gradients only when transformer is actively training and not frozen)
        grad_enabled = bool(self.transformer.training) and not self.freeze_transformer
        with torch.set_grad_enabled(grad_enabled):
            outputs = self.transformer(input_ids=input_ids, attention_mask=attention_mask)
        
        device = next(self.tcnae.parameters()).device
        original_embeddings = outputs.last_hidden_state.to(device)
        x = original_embeddings.permute(0, 2, 1)
        
        # 2. TCNAE Pass
        reconstructed_x, latent, physics_states = self.tcnae(x)
        reconstruction = reconstructed_x.permute(0, 2, 1)
        
        if return_physics_residuals:
            from src.physics.traffic_loss import TrafficPhysicsLoss
            engine = self.physics_engine or TrafficPhysicsLoss(max_acceleration=10.0)
            physics_residuals = engine.compute_losses(
                physics_states,
                semantic_type=semantic_type,
                **kwargs
            )
            return reconstruction, original_embeddings, physics_residuals
            
        return reconstruction, original_embeddings, physics_states
