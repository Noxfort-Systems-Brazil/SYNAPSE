# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from dataclasses import dataclass
from typing import Optional, Tuple
import torch


@dataclass
class SparseGraphTransitions:
    """
    O(|E|) sparse representation of forward and backward damped random-walk transitions.
    Preserves full autograd, AMP (BF16/FP16), and torch.compile compatibility via
    native gather + scatter_add message passing without allocating N x N dense matrices.
    """
    num_nodes: int
    src: torch.Tensor
    dst: torch.Tensor
    w_forward: torch.Tensor
    w_backward: torch.Tensor
    p_f_row_sum: torch.Tensor
    p_b_row_sum: torch.Tensor
    deg_out_pos: torch.Tensor
    deg_in_pos: torch.Tensor
    is_identity_fallback: bool = False


def sparse_edge_propagate(
    x: torch.Tensor,
    gather_idx: torch.Tensor,
    scatter_idx: torch.Tensor,
    edge_weight: torch.Tensor,
    num_nodes: int,
) -> torch.Tensor:
    """
    Computes sparse matrix-tensor multiplication Y[scatter_idx] += edge_weight * X[gather_idx]
    in O(|E| * C) time and memory across 1D [N], 2D [N, C], or 3D [B, N, C] tensors.
    """
    if gather_idx.numel() == 0:
        return torch.zeros_like(x)

    w = edge_weight.to(dtype=x.dtype)
    if x.dim() == 1:
        msg = x.index_select(0, gather_idx) * w
        out = torch.zeros(num_nodes, dtype=x.dtype, device=x.device)
        out.scatter_add_(0, scatter_idx, msg)
        return out
    elif x.dim() == 2:
        msg = x.index_select(0, gather_idx) * w.unsqueeze(-1)
        out = torch.zeros((num_nodes, x.size(1)), dtype=x.dtype, device=x.device)
        idx = scatter_idx.unsqueeze(-1).expand_as(msg)
        out.scatter_add_(0, idx, msg)
        return out
    elif x.dim() == 3:
        msg = x.index_select(1, gather_idx) * w.view(1, -1, 1)
        out = torch.zeros((x.size(0), num_nodes, x.size(2)), dtype=x.dtype, device=x.device)
        idx = scatter_idx.view(1, -1, 1).expand_as(msg)
        out.scatter_add_(1, idx, msg)
        return out
    else:
        raise ValueError(f"Unsupported tensor rank for sparse_edge_propagate: {x.dim()}")


def compute_sparse_transition_matrices(
    num_nodes: int,
    edge_index: torch.Tensor,
    edge_weight: Optional[torch.Tensor] = None,
    device: torch.device = torch.device("cpu"),
    damping_factor: float = 1.0,
) -> SparseGraphTransitions:
    """
    Computes O(|E|) forward and backward damped random-walk transition operators:
    - Forward walk (P_f @ X)[u] = sum_{e=(u->v)} (gamma * w_e / d_out[u]) * X[v]
    - Backward walk (P_b @ X)[v] = sum_{e=(u->v)} (gamma * w_e / d_in[v]) * X[u]
    """
    if edge_index.numel() == 0 or edge_index.size(1) == 0:
        empty_idx = torch.empty(0, dtype=torch.long, device=device)
        empty_w = torch.empty(0, dtype=torch.float32, device=device)
        ones_n = torch.ones(num_nodes, dtype=torch.float32, device=device)
        return SparseGraphTransitions(
            num_nodes=num_nodes,
            src=empty_idx,
            dst=empty_idx,
            w_forward=empty_w,
            w_backward=empty_w,
            p_f_row_sum=ones_n,
            p_b_row_sum=ones_n,
            deg_out_pos=ones_n,
            deg_in_pos=ones_n,
            is_identity_fallback=True,
        )

    src = edge_index[0].to(device)
    dst = edge_index[1].to(device)
    weights = (
        edge_weight.to(device=device, dtype=torch.float32)
        if edge_weight is not None
        else torch.ones(src.size(0), dtype=torch.float32, device=device)
    )

    # Deduplicate (src, dst) pairs if present (matching dense index_put overwrite semantics)
    if src.numel() > 1 and num_nodes > 0:
        flat_idx = src * num_nodes + dst
        unique_flat, inv = torch.unique(flat_idx, return_inverse=True)
        if unique_flat.numel() != flat_idx.numel():
            dedup_w = torch.zeros(unique_flat.numel(), dtype=weights.dtype, device=device)
            order = torch.arange(flat_idx.numel(), device=device)
            max_order = torch.zeros(unique_flat.numel(), dtype=torch.long, device=device)
            max_order.scatter_reduce_(0, inv, order, reduce="amax", include_self=False)
            dedup_w = weights.index_select(0, max_order)
            src = unique_flat // num_nodes
            dst = unique_flat % num_nodes
            weights = dedup_w

    d_out = torch.zeros(num_nodes, dtype=weights.dtype, device=device)
    d_out.scatter_add_(0, src, weights)
    d_out_inv = torch.where(d_out > 0, 1.0 / d_out, torch.zeros_like(d_out))
    w_forward = damping_factor * weights * d_out_inv.index_select(0, src)

    d_in = torch.zeros(num_nodes, dtype=weights.dtype, device=device)
    d_in.scatter_add_(0, dst, weights)
    d_in_inv = torch.where(d_in > 0, 1.0 / d_in, torch.zeros_like(d_in))
    w_backward = damping_factor * weights * d_in_inv.index_select(0, dst)

    p_f_row_sum = torch.zeros(num_nodes, dtype=weights.dtype, device=device)
    p_f_row_sum.scatter_add_(0, src, w_forward)

    p_b_row_sum = torch.zeros(num_nodes, dtype=weights.dtype, device=device)
    p_b_row_sum.scatter_add_(0, dst, w_backward)

    deg_out_pos = torch.zeros(num_nodes, dtype=weights.dtype, device=device)
    deg_out_pos.scatter_add_(0, src, (w_forward > 0).float())

    deg_in_pos = torch.zeros(num_nodes, dtype=weights.dtype, device=device)
    deg_in_pos.scatter_add_(0, dst, (w_backward > 0).float())

    return SparseGraphTransitions(
        num_nodes=num_nodes,
        src=src,
        dst=dst,
        w_forward=w_forward,
        w_backward=w_backward,
        p_f_row_sum=p_f_row_sum,
        p_b_row_sum=p_b_row_sum,
        deg_out_pos=deg_out_pos,
        deg_in_pos=deg_in_pos,
        is_identity_fallback=False,
    )


def compute_random_walk_transition_matrices(
    num_nodes: int,
    edge_index: torch.Tensor,
    edge_weight: Optional[torch.Tensor] = None,
    device: torch.device = torch.device('cpu'),
    damping_factor: float = 1.0
) -> Tuple[torch.Tensor, torch.Tensor]:
    r"""
    Computes forward and backward normalized random-walk transition matrices with optional damping.
    
    Formulas:
    1. Forward Random Walk (Downstream flow): P_f = \gamma * (D_o^{-1} * A)
    2. Backward Random Walk (Upstream wave/congestion): P_b = \gamma * (D_i^{-1} * A^T)
    where \gamma is the damping factor representing absorption/permeability (sinks/sources).
    
    Optimized: Eliminates O(N^3) `torch.diag(d_inv) @ adj` matrix multiplications in favor
    of O(N^2) vectorized row broadcasting.
    """
    if edge_index.numel() == 0 or edge_index.size(1) == 0:
        # Fallback for disconnected graph
        identity = torch.eye(num_nodes, device=device)
        return identity, identity

    # Build dense adjacency
    adj = torch.zeros((num_nodes, num_nodes), device=device)
    src, dst = edge_index[0].to(device), edge_index[1].to(device)
    
    weights = edge_weight.to(device) if edge_weight is not None else torch.ones_like(src, dtype=torch.float, device=device)
    adj.index_put_((src, dst), weights)

    # Forward transition (Out-degree normalization: P_f = \gamma * D_out^{-1} * A) via O(N^2) row scaling
    d_out = adj.sum(dim=1)
    d_out_inv = torch.where(d_out > 0, 1.0 / d_out, torch.zeros_like(d_out))
    p_forward = (damping_factor * d_out_inv).unsqueeze(1) * adj

    # Backward transition (In-degree normalization of transpose: P_b = \gamma * D_in^{-1} * A^T)
    adj_t = adj.t()
    d_in = adj_t.sum(dim=1)
    d_in_inv = torch.where(d_in > 0, 1.0 / d_in, torch.zeros_like(d_in))
    p_backward = (damping_factor * d_in_inv).unsqueeze(1) * adj_t

    return p_forward, p_backward


def batch_offset_edge_index(
    edge_index: torch.Tensor,
    batch_size: int,
    num_nodes: int,
    device: torch.device = torch.device('cpu')
) -> torch.Tensor:
    """
    Replicates and offsets COO edge_index across multiple graphs in a mini-batch
    using vectorized broadcasting (zero Python loop).
    """
    if edge_index.numel() == 0 or edge_index.size(1) == 0:
        return edge_index.to(device)
        
    if batch_size == 1:
        return edge_index.to(device)

    base_edges = edge_index.to(device)
    offsets = (torch.arange(batch_size, device=device, dtype=base_edges.dtype) * num_nodes).view(1, batch_size, 1)
    batched = base_edges.unsqueeze(1) + offsets  # [2, Batch, Num_Edges]
    return batched.reshape(2, -1)
