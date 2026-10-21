# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Optional
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


class GraphLaplacianSpectralConv(nn.Module):
    r"""
    Spectral Graph Convolution Layer based on Graph Laplacian Chebyshev Polynomials.
    
    Provides permutation-equivariant spectral filtering over arbitrary graph topologies
    (Defferrard et al., 2016 / Hammond et al., 2011).
    Unlike naive 1D FFT over graph node indices, this operator respects the physical
    graph connectivity:
        Y = sum_{k=0}^{K-1} T_k(\tilde{L}) @ X @ W_k + bias
    where \tilde{L} = (2 / \lambda_max) * L_sym - I is the scaled normalized Laplacian.
    """

    def __init__(self, in_channels: int, out_channels: int, K: int = 3, bias: bool = True):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.K = K

        self.weights = nn.Parameter(
            torch.empty(K, in_channels, out_channels, dtype=torch.float32)
        )
        if bias:
            self.bias = nn.Parameter(torch.empty(out_channels, dtype=torch.float32))
        else:
            self.register_parameter("bias", None)

        self.reset_parameters()

    def reset_parameters(self):
        for k in range(self.K):
            nn.init.xavier_uniform_(self.weights[k])
        if self.bias is not None:
            nn.init.zeros_(self.bias)

    @staticmethod
    def compute_scaled_laplacian(
        num_nodes: int,
        edge_index: torch.Tensor,
        edge_weight: Optional[torch.Tensor] = None,
        device: torch.device = torch.device("cpu")
    ) -> torch.Tensor:
        r"""
        Computes scaled normalized Laplacian: \tilde{L} = L_sym - I = - D^{-1/2} A D^{-1/2}
        (assuming \lambda_max = 2.0).
        """
        if edge_index.numel() == 0 or edge_index.size(1) == 0:
            return torch.zeros((num_nodes, num_nodes), device=device)

        src, dst = edge_index[0].to(device), edge_index[1].to(device)
        adj = torch.zeros((num_nodes, num_nodes), device=device)
        weights = edge_weight.to(device) if edge_weight is not None else torch.ones_like(src, dtype=torch.float, device=device)
        adj.index_put_((src, dst), weights)

        # Symmetrize adjacency for undirected spectral diffusion: A_sym = max(A, A^T)
        adj_sym = torch.maximum(adj, adj.t())

        # Degree
        deg = adj_sym.sum(dim=1)
        deg_inv_sqrt = torch.where(deg > 0, 1.0 / torch.sqrt(deg), torch.zeros_like(deg))
        d_mat = torch.diag(deg_inv_sqrt)

        # Normalized adjacency: A_norm = D^{-1/2} A_sym D^{-1/2}
        a_norm = d_mat @ adj_sym @ d_mat

        # L_sym = I - A_norm
        # \tilde{L} = (2 / \lambda_max) * L_sym - I = (L_sym - I) = - A_norm (with \lambda_max = 2.0)
        l_tilde = -a_norm
        return l_tilde

    def forward(
        self,
        x: torch.Tensor,
        edge_index: Optional[torch.Tensor] = None,
        edge_weight: Optional[torch.Tensor] = None,
        l_tilde: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Args:
            x: Node features [Batch, Num_Nodes, In_Channels] or [Batch, In_Channels, Num_Nodes]
            edge_index: Graph connectivity [2, Num_Edges]
            edge_weight: Optional edge weights [Num_Edges]
            l_tilde: Precomputed scaled Laplacian [Num_Nodes, Num_Nodes]
        Returns:
            out: Filtered node features [Batch, Num_Nodes, Out_Channels] (or matching permute)
        """
        is_channel_second = False
        if x.dim() == 3 and x.size(1) == self.in_channels and x.size(2) != self.in_channels:
            # [Batch, In_Channels, Num_Nodes] -> [Batch, Num_Nodes, In_Channels]
            x = x.permute(0, 2, 1)
            is_channel_second = True

        batch_size, num_nodes, in_dim = x.shape
        device = x.device

        if l_tilde is None:
            if edge_index is not None and edge_index.numel() > 0:
                l_tilde = self.compute_scaled_laplacian(num_nodes, edge_index, edge_weight, device=device)
            else:
                l_tilde = torch.zeros((num_nodes, num_nodes), device=device)

        # Chebyshev recursion
        # T_0(X) = X
        t0 = x
        out = torch.matmul(t0, self.weights[0])

        if self.K > 1:
            # T_1(X) = \tilde{L} @ X
            t1 = torch.matmul(l_tilde, x)
            out = out + torch.matmul(t1, self.weights[1])

            for k in range(2, self.K):
                # T_k(X) = 2 * \tilde{L} @ T_{k-1} - T_{k-2}
                tk = 2.0 * torch.matmul(l_tilde, t1) - t0
                out = out + torch.matmul(tk, self.weights[k])
                t0 = t1
                t1 = tk

        if self.bias is not None:
            out = out + self.bias

        if is_channel_second:
            out = out.permute(0, 2, 1)

        return out


__all__ = [
    "SpectralConv1d",
    "SpectralConv2d",
    "GraphLaplacianSpectralConv",
]

