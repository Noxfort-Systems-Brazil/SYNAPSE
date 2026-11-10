# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import torch
import torch.nn as nn
from typing import Optional, Tuple
import torch.nn.functional as F

try:
    from torch.nn.utils.parametrizations import weight_norm
except ImportError:
    from torch.nn.utils import weight_norm


class Chomp1d(nn.Module):
    """
    Utility layer to crop the output of a Conv1d to ensure causal padding.
    Removes the extra padding from the right (future) timesteps.
    """
    def __init__(self, chomp_size: int):
        super(Chomp1d, self).__init__()
        self.chomp_size = chomp_size

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if self.chomp_size == 0:
            return x
        return x[:, :, :-self.chomp_size].contiguous()


class CausalConv1d(nn.Module):
    """
    Causal 1D Convolution with parameterized weight normalization.
    Trims future padding dynamically to guarantee strict temporal causality.
    """
    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        stride: int = 1,
        dilation: int = 1
    ):
        super().__init__()
        self.padding = (kernel_size - 1) * dilation
        self.conv = weight_norm(
            nn.Conv1d(
                in_channels=in_channels,
                out_channels=out_channels,
                kernel_size=kernel_size,
                stride=stride,
                padding=self.padding,
                dilation=dilation
            )
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.conv(x)
        if self.padding > 0:
            out = out[:, :, :-self.padding].contiguous()
        return out


class TemporalBlock(nn.Module):
    """
    Dilated Causal Temporal Residual Block.
    
    Structure:
    Input -> [Dilated Causal Conv -> Chomp/Trim -> ReLU -> Dropout] x2 -> Output
          \\_____________________________________________________________/
                                         |
                            Residual Link (1x1 Conv if channel dimensions differ)
    """
    def __init__(
        self,
        n_inputs: int,
        n_outputs: int,
        kernel_size: int,
        stride: int = 1,
        dilation: int = 1,
        padding: Optional[int] = None,
        dropout: float = 0.1
    ):
        super(TemporalBlock, self).__init__()
        
        self.pad_val = (kernel_size - 1) * dilation if padding is None else padding
        
        # --- First Conv Layer ---
        self.conv1 = weight_norm(nn.Conv1d(
            n_inputs, n_outputs, kernel_size,
            stride=stride, padding=self.pad_val, dilation=dilation
        ))
        self.chomp1 = Chomp1d(self.pad_val)
        self.relu1 = nn.ReLU()
        self.dropout1 = nn.Dropout(dropout)

        # --- Second Conv Layer ---
        self.conv2 = weight_norm(nn.Conv1d(
            n_outputs, n_outputs, kernel_size,
            stride=stride, padding=self.pad_val, dilation=dilation
        ))
        self.chomp2 = Chomp1d(self.pad_val)
        self.relu2 = nn.ReLU()
        self.dropout2 = nn.Dropout(dropout)

        self.net = nn.Sequential(
            self.conv1, self.chomp1, self.relu1, self.dropout1,
            self.conv2, self.chomp2, self.relu2, self.dropout2
        )
        
        # --- Residual Connection ---
        self.downsample = nn.Conv1d(n_inputs, n_outputs, 1) if n_inputs != n_outputs else None
        self.relu = nn.ReLU()
        self.init_weights()

    def init_weights(self):
        """Initialize weights with normal distribution."""
        self.conv1.weight.data.normal_(0, 0.01)
        self.conv2.weight.data.normal_(0, 0.01)
        if self.downsample is not None:
            self.downsample.weight.data.normal_(0, 0.01)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.net(x)
        res = x if self.downsample is None else self.downsample(x)
        return self.relu(out + res)

    def step(
        self,
        x_t: torch.Tensor,
        state: Optional[dict] = None
    ) -> Tuple[torch.Tensor, dict]:
        """
        Incremental causal step evaluation O(1) for a single timestep x_t.
        Eliminates re-convolving through the full historical sequence window.
        """
        b_size = x_t.size(0)
        device = x_t.device
        dtype = x_t.dtype

        if state is None:
            buf1 = torch.zeros(b_size, self.conv1.in_channels, self.pad_val, device=device, dtype=dtype)
            buf2 = torch.zeros(b_size, self.conv2.in_channels, self.pad_val, device=device, dtype=dtype)
        else:
            buf1 = state.get("buf1")
            buf2 = state.get("buf2")
            if buf1 is None or buf1.size(0) != b_size or buf1.device != device:
                buf1 = torch.zeros(b_size, self.conv1.in_channels, self.pad_val, device=device, dtype=dtype)
            if buf2 is None or buf2.size(0) != b_size or buf2.device != device:
                buf2 = torch.zeros(b_size, self.conv2.in_channels, self.pad_val, device=device, dtype=dtype)

        if self.pad_val > 0:
            in1 = torch.cat([buf1, x_t], dim=-1)
            new_buf1 = in1[:, :, 1:]
            c1 = F.conv1d(in1, self.conv1.weight, self.conv1.bias, stride=self.conv1.stride, dilation=self.conv1.dilation)
        else:
            new_buf1 = buf1
            c1 = F.conv1d(x_t, self.conv1.weight, self.conv1.bias, stride=self.conv1.stride, dilation=self.conv1.dilation)

        r1 = self.relu1(self.dropout1(c1))

        if self.pad_val > 0:
            in2 = torch.cat([buf2, r1], dim=-1)
            new_buf2 = in2[:, :, 1:]
            c2 = F.conv1d(in2, self.conv2.weight, self.conv2.bias, stride=self.conv2.stride, dilation=self.conv2.dilation)
        else:
            new_buf2 = buf2
            c2 = F.conv1d(r1, self.conv2.weight, self.conv2.bias, stride=self.conv2.stride, dilation=self.conv2.dilation)

        r2 = self.relu2(self.dropout2(c2))

        res = x_t if self.downsample is None else self.downsample(x_t)
        out_t = self.relu(r2 + res)

        return out_t, {"buf1": new_buf1, "buf2": new_buf2}
