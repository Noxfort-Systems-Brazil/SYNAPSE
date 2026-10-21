# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Optional
import torch
import torch.nn as nn
import torch.nn.functional as F

from src.blocks.spectral_blocks import SpectralConv1d


class SpectralFeatureBlock(nn.Module):
    """
    Fourier Spectral Feature Block.
    Drop-in replacement for TimesNet in PeakClassifierAgent and PeakPipeline.
    Extracts periodic patterns across multi-scale frequency bands using FFT.
    """

    def __init__(
        self,
        enc_in: int = 2,
        d_model: int = 64,
        seq_len: int = 2048,
        modes: int = 32,
        **kwargs
    ):
        super().__init__()
        self.enc_in = enc_in
        self.d_model = d_model
        self.seq_len = seq_len

        self.conv_in = nn.Conv1d(enc_in, d_model, 1)
        self.spectral_conv = SpectralConv1d(d_model, d_model, modes1=modes)
        self.fc_out = nn.Sequential(
            nn.Conv1d(d_model, d_model, 3, padding=1),
            nn.GELU(),
            nn.Conv1d(d_model, enc_in, 1)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Input tensor [Batch, SeqLen, Channels] or [Batch, Channels, SeqLen]
        Returns:
            features: [Batch, SeqLen, Channels]
        """
        is_seq_first = False
        if x.dim() == 3 and x.size(1) != self.enc_in and x.size(2) == self.enc_in:
            x = x.permute(0, 2, 1)
            is_seq_first = True

        h = self.conv_in(x)
        h_spec = self.spectral_conv(h)
        out = self.fc_out(F.gelu(h + h_spec))

        if is_seq_first:
            out = out.permute(0, 2, 1)

        return out


# Alias for backwards compatibility
SpectralFeatureExtractor = SpectralFeatureBlock

__all__ = ["SpectralFeatureBlock", "SpectralFeatureExtractor"]
