# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Tuple, Optional, Union

from src.blocks.temporal_blocks import Chomp1d, TemporalBlock

# Enable Tensor Cores globally for matrix multiplications and cuDNN operations
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True


class TCNAEEncoder(nn.Module):
    """
    Lightweight Causal TCN Encoder.
    Compresses an input sequence [Batch, Channels, SeqLen] into a latent representation [Batch, LatentDim].
    """
    def __init__(
        self,
        num_inputs: int = 1,
        num_channels: Optional[List[int]] = None,
        latent_dim: int = 32,
        kernel_size: int = 2,
        dropout: float = 0.1
    ):
        super(TCNAEEncoder, self).__init__()
        num_channels = num_channels or [8, 16]
        layers = []
        num_levels = len(num_channels)
        
        for i in range(num_levels):
            dilation_size = 2 ** i
            in_channels = num_inputs if i == 0 else num_channels[i - 1]
            out_channels = num_channels[i]
            padding = (kernel_size - 1) * dilation_size
            layers.append(TemporalBlock(
                n_inputs=in_channels,
                n_outputs=out_channels,
                kernel_size=kernel_size,
                stride=1,
                dilation=dilation_size,
                padding=padding,
                dropout=dropout
            ))
            
        self.network = nn.Sequential(*layers)
        self.latent_proj = nn.Conv1d(num_channels[-1], latent_dim, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Returns:
            latent: [Batch, LatentDim, SeqLen]
        """
        features = self.network(x)
        latent = self.latent_proj(features)
        return latent

    def step(
        self,
        x_t: torch.Tensor,
        state: Optional[dict] = None
    ) -> Tuple[torch.Tensor, dict]:
        """
        Incremental step encoding O(1) for a single timestep x_t.
        """
        block_states = state.get("blocks") if state is not None else None
        new_block_states = []
        feat = x_t
        for i, block in enumerate(self.network):
            b_state = block_states[i] if block_states and i < len(block_states) else None
            feat, next_b_state = block.step(feat, b_state)
            new_block_states.append(next_b_state)

        latent_t = self.latent_proj(feat)
        return latent_t, {"blocks": new_block_states}



class TCNAEDecoder(nn.Module):
    """
    Lightweight Causal TCN Decoder.
    Reconstructs the original physical traffic signals [Batch, OutputDim, SeqLen] from the latent space.
    """
    def __init__(
        self,
        latent_dim: int = 32,
        num_channels: Optional[List[int]] = None,
        num_outputs: int = 1,
        kernel_size: int = 2,
        dropout: float = 0.1
    ):
        super(TCNAEDecoder, self).__init__()
        channels = list(reversed(num_channels or [8, 16]))
        self.input_proj = nn.Conv1d(latent_dim, channels[0], kernel_size=1)
        
        layers = []
        for i in range(len(channels)):
            dilation_size = 2 ** (len(channels) - 1 - i)
            in_channels = channels[i]
            out_channels = channels[i + 1] if i + 1 < len(channels) else channels[-1]
            padding = (kernel_size - 1) * dilation_size
            layers.append(TemporalBlock(
                n_inputs=in_channels,
                n_outputs=out_channels,
                kernel_size=kernel_size,
                stride=1,
                dilation=dilation_size,
                padding=padding,
                dropout=dropout
            ))
            
        self.network = nn.Sequential(*layers)
        self.reconstruct_head = nn.Conv1d(channels[-1], num_outputs, kernel_size=1)

    def forward(self, z: torch.Tensor) -> torch.Tensor:
        """
        Returns:
            reconstructed: [Batch, OutputDim, SeqLen]
        """
        h = self.input_proj(z)
        features = self.network(h)
        return self.reconstruct_head(features)


class TCNAE(nn.Module):
    """
    Pure Temporal Convolutional Autoencoder (TCN-AE).
    
    A clean neural network architecture for node-level temporal feature extraction and compression:
    - Ultra-compact parameter footprint (~3.000 parameters / < 20 KB VRAM).
    - Causal dilated convolutions guaranteeing zero temporal leakage.
    - Pure computational graph adhering strictly to SOLID.
    """
    def __init__(
        self,
        num_inputs: int = 1,
        num_channels: Optional[List[int]] = None,
        latent_dim: int = 32,
        kernel_size: int = 2,
        dropout: float = 0.1
    ):
        super(TCNAE, self).__init__()
        self.num_inputs = num_inputs
        self.num_channels = num_channels or [8, 16]
        self.latent_dim = latent_dim
        self.kernel_size = kernel_size
        self.dropout = dropout

        self.encoder = TCNAEEncoder(
            num_inputs=num_inputs,
            num_channels=self.num_channels,
            latent_dim=latent_dim,
            kernel_size=kernel_size,
            dropout=dropout
        )
        self.decoder = TCNAEDecoder(
            latent_dim=latent_dim,
            num_channels=self.num_channels,
            num_outputs=num_inputs,
            kernel_size=kernel_size,
            dropout=dropout
        )

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        """
        Extracts the latent embedding for the sequence.
        
        Args:
            x: Tensor [Batch, Channels, SeqLen]
        Returns:
            z: Latent embedding vector at the last timestep [Batch, LatentDim]
        """
        latent_seq = self.encoder(x)
        return latent_seq[:, :, -1]

    def decode(self, z: torch.Tensor, seq_len: int) -> torch.Tensor:
        """
        Reconstructs the sequence from a latent vector.
        
        Args:
            z: Latent embedding [Batch, LatentDim]
            seq_len: Target sequence length to expand
        Returns:
            reconstructed: [Batch, Channels, SeqLen]
        """
        z_expanded = z.unsqueeze(-1).expand(-1, -1, seq_len)
        return self.decoder(z_expanded)

    def forward(
        self,
        x: torch.Tensor,
        return_embedding: bool = True
    ) -> Union[torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]:
        """
        Full Autoencoder forward pass.
        
        Args:
            x: Input tensor [Batch, Channels, SeqLen]
            return_embedding: Whether to return (reconstructed, latent_embedding)
        Returns:
            reconstructed: [Batch, Channels, SeqLen]
            (optional) embedding: [Batch, LatentDim]
        """
        latent_seq = self.encoder(x)
        reconstructed = self.decoder(latent_seq)
        
        if return_embedding:
            embedding = latent_seq[:, :, -1]
            return reconstructed, embedding
        return reconstructed

    def step(
        self,
        x_t: torch.Tensor,
        state: Optional[dict] = None
    ) -> Tuple[torch.Tensor, dict]:
        """
        Incremental O(1) feature encoding for real-time sensor ingestion.
        
        Args:
            x_t: Tensor [Batch, Channels] or [Batch, Channels, 1]
            state: Optional cached dict of previous states
        Returns:
            latent: [Batch, LatentDim] (matches .encode(x) shape)
            new_state: Updated state dict for subsequent steps
        """
        if x_t.dim() == 2:
            x_t = x_t.unsqueeze(-1)
        latent_t, new_state = self.encoder.step(x_t, state=state)
        return latent_t.squeeze(-1), new_state



# Compatibility Alias
TemporalConvNet = TCNAE
