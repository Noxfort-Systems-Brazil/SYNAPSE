# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Graph Laplacian Chebyshev Spectral Convolution Layers.
Enables permutation-equivariant spectral filtering over arbitrary and dynamic road graph topologies.
"""

from typing import Optional, Tuple
import torch
import torch.nn as nn
from src.utils.graph_utils import sparse_edge_propagate

# Enable Tensor Cores globally for matrix multiplications and cuDNN operations
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True


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
        (assuming \lambda_max = 2.0) via O(N^2) broadcasting without O(N^3) torch.diag matmuls.
        """
        if edge_index.numel() == 0 or edge_index.size(1) == 0:
            return torch.zeros((num_nodes, num_nodes), device=device)

        src, dst = edge_index[0].to(device), edge_index[1].to(device)
        adj = torch.zeros((num_nodes, num_nodes), device=device)
        weights = edge_weight.to(device) if edge_weight is not None else torch.ones_like(src, dtype=torch.float, device=device)
        adj.index_put_((src, dst), weights)

        # Symmetrize adjacency for undirected spectral diffusion: A_sym = max(A, A^T)
        adj_sym = torch.maximum(adj, adj.t())

        # Degree & O(N^2) elementwise scaling instead of d_mat @ adj_sym @ d_mat
        deg = adj_sym.sum(dim=1)
        deg_inv_sqrt = torch.where(deg > 0, torch.rsqrt(deg), torch.zeros_like(deg))
        a_norm = deg_inv_sqrt.unsqueeze(1) * adj_sym * deg_inv_sqrt.unsqueeze(0)

        return -a_norm

    @staticmethod
    def compute_sparse_laplacian_edges(
        num_nodes: int,
        edge_index: Optional[torch.Tensor],
        edge_weight: Optional[torch.Tensor] = None,
        device: torch.device = torch.device("cpu")
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        r"""
        Computes sparse symmetrized scaled Laplacian edges (sym_src, sym_dst, lap_weights)
        matching \tilde{L} = - D^{-1/2} max(A, A^T) D^{-1/2} in O(|E| log |E|) without N x N memory.
        """
        if edge_index is None or edge_index.numel() == 0 or edge_index.size(1) == 0 or num_nodes <= 0:
            empty_i = torch.empty(0, dtype=torch.long, device=device)
            empty_w = torch.empty(0, dtype=torch.float32, device=device)
            return empty_i, empty_i, empty_w

        src = edge_index[0].to(device)
        dst = edge_index[1].to(device)
        weights = (
            edge_weight.to(device=device, dtype=torch.float32)
            if edge_weight is not None
            else torch.ones(src.size(0), dtype=torch.float32, device=device)
        )

        # 1. Deduplicate directed edges (matching index_put overwrite semantics)
        if src.numel() > 1:
            flat_dir = src * num_nodes + dst
            unique_dir, inv_dir = torch.unique(flat_dir, return_inverse=True)
            if unique_dir.numel() != flat_dir.numel():
                order = torch.arange(flat_dir.numel(), device=device)
                max_order = torch.zeros(unique_dir.numel(), dtype=torch.long, device=device)
                max_order.scatter_reduce_(0, inv_dir, order, reduce="amax", include_self=False)
                weights = weights.index_select(0, max_order)
                src = unique_dir // num_nodes
                dst = unique_dir % num_nodes

        # 2. Symmetrize via max(A, A^T) over directed union
        all_u = torch.cat([src, dst], dim=0)
        all_v = torch.cat([dst, src], dim=0)
        all_w = torch.cat([weights, weights], dim=0)

        flat_sym = all_u * num_nodes + all_v
        unique_sym, inv_sym = torch.unique(flat_sym, return_inverse=True)
        sym_w = torch.zeros(unique_sym.numel(), dtype=weights.dtype, device=device)
        sym_w.scatter_reduce_(0, inv_sym, all_w, reduce="amax", include_self=False)

        sym_u = unique_sym // num_nodes
        sym_v = unique_sym % num_nodes

        # 3. Symmetric normalization: - deg[u]^{-1/2} * sym_w * deg[v]^{-1/2}
        deg = torch.zeros(num_nodes, dtype=weights.dtype, device=device)
        deg.scatter_add_(0, sym_u, sym_w)
        deg_inv_sqrt = torch.where(deg > 0, torch.rsqrt(deg), torch.zeros_like(deg))
        lap_w = -deg_inv_sqrt.index_select(0, sym_u) * sym_w * deg_inv_sqrt.index_select(0, sym_v)

        return sym_u, sym_v, lap_w

    def forward(
        self,
        x: torch.Tensor,
        edge_index: Optional[torch.Tensor] = None,
        edge_weight: Optional[torch.Tensor] = None,
        l_tilde: Optional[torch.Tensor] = None,
        sparse_laplacian: Optional[Tuple[torch.Tensor, torch.Tensor, torch.Tensor]] = None,
    ) -> torch.Tensor:
        """
        Args:
            x: Node features [Batch, Num_Nodes, In_Channels] or [Batch, In_Channels, Num_Nodes]
            edge_index: Graph connectivity [2, Num_Edges]
            edge_weight: Optional edge weights [Num_Edges]
            l_tilde: Optional precomputed dense scaled Laplacian [Num_Nodes, Num_Nodes]
            sparse_laplacian: Optional precomputed sparse tuple (sym_u, sym_v, lap_w) for O(|E|) execution
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

        use_dense = l_tilde is not None
        if not use_dense and sparse_laplacian is None:
            sparse_laplacian = self.compute_sparse_laplacian_edges(
                num_nodes=num_nodes,
                edge_index=edge_index,
                edge_weight=edge_weight,
                device=device,
            )

        # Chebyshev recursion: T_0(X) = X
        t0 = x
        out = torch.matmul(t0, self.weights[0].to(dtype=x.dtype))

        if self.K > 1:
            if use_dense:
                l_dense = l_tilde.to(dtype=x.dtype)
                t1 = torch.matmul(l_dense, x)
                out = out + torch.matmul(t1, self.weights[1].to(dtype=x.dtype))

                for k in range(2, self.K):
                    tk = 2.0 * torch.matmul(l_dense, t1) - t0
                    out = out + torch.matmul(tk, self.weights[k].to(dtype=x.dtype))
                    t0 = t1
                    t1 = tk
            else:
                sym_u, sym_v, lap_w = sparse_laplacian  # type: ignore[misc]
                t1 = sparse_edge_propagate(x, gather_idx=sym_v, scatter_idx=sym_u, edge_weight=lap_w, num_nodes=num_nodes)
                out = out + torch.matmul(t1, self.weights[1].to(dtype=x.dtype))

                for k in range(2, self.K):
                    l_t1 = sparse_edge_propagate(t1, gather_idx=sym_v, scatter_idx=sym_u, edge_weight=lap_w, num_nodes=num_nodes)
                    tk = 2.0 * l_t1 - t0
                    out = out + torch.matmul(tk, self.weights[k].to(dtype=x.dtype))
                    t0 = t1
                    t1 = tk

        if self.bias is not None:
            out = out + self.bias.to(dtype=out.dtype)

        if is_channel_second:
            out = out.permute(0, 2, 1)

        return out


__all__ = [
    "GraphLaplacianSpectralConv",
]
