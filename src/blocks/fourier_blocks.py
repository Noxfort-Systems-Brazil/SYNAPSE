# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
1D and 2D Fourier Neural Operator (FNO) Spectral Convolution Layers.
Enables continuous spatiotemporal coordinate and sequence modeling in Euclidean domains.
"""

import torch
import torch.nn as nn

# Enable Tensor Cores globally for matrix multiplications and cuDNN operations
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True


class SpectralConv1d(nn.Module):
    """
    1D Fourier Spectral Convolution Layer.
    Computes FFT -> Complex Multiplication on Lower Modes -> IFFT.
    Stores real and imaginary weights as float32 tensors for AMP GradScaler compatibility.
    """

    def __init__(self, in_channels: int, out_channels: int, modes1: int):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.modes1 = modes1

        scale = 1.0 / (in_channels * out_channels)
        self.weights_real = nn.Parameter(
            scale * torch.randn(in_channels, out_channels, modes1, dtype=torch.float32)
        )
        self.weights_imag = nn.Parameter(
            scale * torch.randn(in_channels, out_channels, modes1, dtype=torch.float32)
        )

    def compl_mul1d(self, input_tensor: torch.Tensor, weights: torch.Tensor) -> torch.Tensor:
        """(batch, in_channel, x), (in_channel, out_channel, x) -> (batch, out_channel, x)"""
        return torch.einsum("bix,iox->box", input_tensor, weights)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [Batch, Channels, SeqLen]
        Returns:
            out: [Batch, Out_Channels, SeqLen]
        """
        batch_size, channels, length = x.shape
        orig_dtype = x.dtype

        # 1. Compute real FFT in float32 for cuFFT stability with non-power-of-2 lengths under AMP
        x_float = x.float()
        x_ft = torch.fft.rfft(x_float)

        # 2. Multiply relevant Fourier modes
        out_ft = torch.zeros(
            batch_size,
            self.out_channels,
            length // 2 + 1,
            device=x.device,
            dtype=torch.cfloat
        )
        modes = min(self.modes1, length // 2 + 1)
        weights = torch.complex(self.weights_real, self.weights_imag)
        out_ft[:, :, :modes] = self.compl_mul1d(x_ft[:, :, :modes], weights[:, :, :modes])

        # 3. Return to physical domain via IFFT
        x_out = torch.fft.irfft(out_ft, n=length)
        return x_out.to(orig_dtype)


class SpectralConv2d(nn.Module):
    """
    2D Fourier Spectral Convolution Layer for Spatiotemporal (x, t) Fields.
    Stores real and imaginary weights as float32 tensors for AMP GradScaler compatibility.
    """

    def __init__(self, in_channels: int, out_channels: int, modes1: int, modes2: int):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.modes1 = modes1
        self.modes2 = modes2

        scale = 1.0 / (in_channels * out_channels)
        self.weights1_real = nn.Parameter(
            scale * torch.randn(in_channels, out_channels, modes1, modes2, dtype=torch.float32)
        )
        self.weights1_imag = nn.Parameter(
            scale * torch.randn(in_channels, out_channels, modes1, modes2, dtype=torch.float32)
        )
        self.weights2_real = nn.Parameter(
            scale * torch.randn(in_channels, out_channels, modes1, modes2, dtype=torch.float32)
        )
        self.weights2_imag = nn.Parameter(
            scale * torch.randn(in_channels, out_channels, modes1, modes2, dtype=torch.float32)
        )

    def compl_mul2d(self, input_tensor: torch.Tensor, weights: torch.Tensor) -> torch.Tensor:
        """(batch, in_channel, x, y), (in_channel, out_channel, x, y) -> (batch, out_channel, x, y)"""
        return torch.einsum("bixy,ioxy->boxy", input_tensor, weights)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [Batch, Channels, Spatial_Dim, Temporal_Dim]
        Returns:
            out: [Batch, Out_Channels, Spatial_Dim, Temporal_Dim]
        """
        batch_size, channels, size_x, size_y = x.shape
        orig_dtype = x.dtype

        x_float = x.float()
        x_ft = torch.fft.rfft2(x_float)

        out_ft = torch.zeros(
            batch_size,
            self.out_channels,
            size_x,
            size_y // 2 + 1,
            device=x.device,
            dtype=torch.cfloat
        )

        modes_x = min(self.modes1, size_x // 2)
        modes_y = min(self.modes2, size_y // 2 + 1)

        weights1 = torch.complex(self.weights1_real, self.weights1_imag)
        weights2 = torch.complex(self.weights2_real, self.weights2_imag)

        out_ft[:, :, :modes_x, :modes_y] = self.compl_mul2d(
            x_ft[:, :, :modes_x, :modes_y], weights1[:, :, :modes_x, :modes_y]
        )
        out_ft[:, :, -modes_x:, :modes_y] = self.compl_mul2d(
            x_ft[:, :, -modes_x:, :modes_y], weights2[:, :, -modes_x:, :modes_y]
        )

        x_out = torch.fft.irfft2(out_ft, s=(size_x, size_y))
        return x_out.to(orig_dtype)


__all__ = [
    "SpectralConv1d",
    "SpectralConv2d",
]
