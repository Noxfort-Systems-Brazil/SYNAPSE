# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Optional
import torch
import torch.nn as nn
import torch.nn.functional as F
from src.interfaces.physics import IPhysicsConstraint


class ContinuumConservation(nn.Module):
    """
    Hydrodynamic Continuum Traffic Model (LWR - Lighthill-Whitham-Richards).
    Enforces consistency between Flow (q), Density (rho/k), and Velocity (v):
        q_expected = rho * v
        Residual: SmoothL1(q / scale, q_expected / scale)
    """

    def __init__(self, penalty_scale: float = 1.0, use_smooth_l1: bool = True):
        super().__init__()
        self.penalty_scale = penalty_scale
        self.use_smooth_l1 = use_smooth_l1

    def compute_residual(
        self,
        q: torch.Tensor,
        v: torch.Tensor,
        rho: torch.Tensor,
        **kwargs
    ) -> torch.Tensor:
        """
        Args:
            q: Flow tensor [Batch, SeqLen] or [Batch, Nodes]
            v: Velocity tensor [Batch, SeqLen] or [Batch, Nodes]
            rho: Density tensor [Batch, SeqLen] or [Batch, Nodes]
        Returns:
            loss_conservation: Scalar conservation residual.
        """
        device = q.device
        q_expected = torch.relu(rho) * torch.relu(v)
        
        if self.use_smooth_l1:
            scale = torch.clamp(torch.mean(torch.abs(q) + 1.0), min=1.0)
            loss = F.smooth_l1_loss(q / scale, q_expected / scale)
        else:
            loss = torch.mean((q - q_expected) ** 2)
            
        return self.penalty_scale * loss


class SpatialGraphConservation(nn.Module):
    """
    Spatial Flow Conservation along Road Graph Edges (Kirchhoff Law for Traffic):
    Enforces Kirchhoff's Current Law for traffic flow at network junctions:
        Sum(flow_in) = Sum(flow_out)
    at every internal intersection/junction node.
    
    Exempts or tolerates boundary nodes (source entries with in_deg=0 and sink exits
    with out_deg=0) to prevent penalizing vehicle ingress and egress at the city borders.
    
    Supports urban permeability slack (permeability_slack / tau_porosidade):
        loss_internal = ReLU(|Sum(flow_in) - Sum(flow_out)| - tau_porosidade)
    which accounts for vehicles entering/leaving garages, residential driveways, and parking
    destinations without artificial closed-pipe divergence penalties.
    """

    def __init__(
        self,
        penalty_scale: float = 1.0,
        boundary_tolerance: Optional[float] = None,
        permeability_slack: float = 0.0
    ):
        super().__init__()
        self.penalty_scale = penalty_scale
        self.boundary_tolerance = boundary_tolerance
        self.permeability_slack = permeability_slack

    def compute_edge_flow(
        self,
        flow: torch.Tensor,
        edge_index: torch.Tensor,
        edge_flow: Optional[torch.Tensor] = None,
        edge_weight: Optional[torch.Tensor] = None,
        num_nodes: Optional[int] = None,
    ) -> torch.Tensor:
        """
        Calculates traffic flow along each directed edge/via.
        
        Args:
            flow: Node flow [Batch, Num_Nodes, 1] or Edge flow [Batch, Num_Edges, 1]
            edge_index: [2, Num_Edges]
            edge_flow: Optional explicit edge flow tensor [Batch, Num_Edges, 1]
            edge_weight: Optional edge routing weights [Num_Edges]
            num_nodes: Optional explicit node count to avoid GPU-to-CPU .item() sync
        Returns:
            q_edges: [Batch, Num_Edges, 1]
        """
        if edge_flow is not None:
            if edge_flow.dim() == 1:
                return edge_flow.unsqueeze(0).unsqueeze(-1)
            elif edge_flow.dim() == 2:
                return edge_flow.unsqueeze(-1)
            return edge_flow

        src = edge_index[0]
        num_edges = edge_index.size(1)

        # Check if flow is already edge-indexed without triggering CUDA stream sync when num_nodes is known
        if num_nodes is not None:
            if flow.size(1) != num_nodes and flow.size(1) == num_edges:
                return flow
            resolved_nodes = num_nodes
        else:
            if flow.size(1) == num_edges and flow.size(1) > 0:
                max_node = int(edge_index.max().detach().cpu()) + 1
                if flow.size(1) != max_node:
                    return flow
            resolved_nodes = flow.size(1)

        # Flow is node-indexed: distribute outflow from source nodes into outgoing edges
        device = flow.device

        # Compute out-degree for each node
        out_deg = torch.zeros(resolved_nodes, dtype=flow.dtype, device=device)
        out_deg.scatter_add_(0, src, torch.ones_like(src, dtype=flow.dtype))

        if edge_weight is not None:
            w = edge_weight.to(device=device, dtype=flow.dtype)
            w_sum = torch.zeros(resolved_nodes, dtype=flow.dtype, device=device)
            w_sum.scatter_add_(0, src, w)
            w_sum_edge = w_sum[src]
            weight_factor = torch.where(
                w_sum_edge > 0,
                w / torch.clamp(w_sum_edge, min=1e-6),
                1.0 / torch.clamp(out_deg[src], min=1.0)
            )
            q_edges = flow[:, src, :] * weight_factor.unsqueeze(0).unsqueeze(-1)
        else:
            denom = torch.clamp(out_deg[src], min=1.0).unsqueeze(0).unsqueeze(-1)
            q_edges = flow[:, src, :] / denom

        return q_edges

    def compute_node_divergence(
        self,
        flow: torch.Tensor,
        edge_index: torch.Tensor,
        edge_flow: Optional[torch.Tensor] = None,
        edge_weight: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Computes signed net divergence: outflow - inflow for each node.
        Used for dynamic continuity equations dk/dt + div(q) = 0.
        """
        if flow.dim() == 1:
            flow = flow.unsqueeze(0).unsqueeze(-1)
        elif flow.dim() == 2:
            flow = flow.unsqueeze(-1)

        device = flow.device
        batch_size = flow.size(0)
        num_nodes = flow.size(1)

        src = edge_index[0].to(device)
        dst = edge_index[1].to(device)

        q_edges = self.compute_edge_flow(flow, edge_index, edge_flow, edge_weight, num_nodes=num_nodes)

        inflow = torch.zeros(batch_size, num_nodes, 1, dtype=q_edges.dtype, device=device)
        outflow = torch.zeros(batch_size, num_nodes, 1, dtype=q_edges.dtype, device=device)

        inflow.index_add_(1, dst, q_edges)
        outflow.index_add_(1, src, q_edges)

        return outflow - inflow

    def compute_residual(
        self,
        flow: torch.Tensor,
        edge_index: Optional[torch.Tensor] = None,
        edge_flow: Optional[torch.Tensor] = None,
        edge_weight: Optional[torch.Tensor] = None,
        boundary_mask: Optional[torch.Tensor] = None,
        boundary_tolerance: Optional[float] = None,
        permeability_slack: Optional[float] = None,
        **kwargs
    ) -> torch.Tensor:
        """
        Computes Kirchhoff's conservation residual across road graph junctions:
            div(v) = |Sigma_in(q_e) - Sigma_out(q_e)|
        with tolerance / exemption for boundary entry (sources) and exit (sinks) nodes,
        and urban permeability slack (tau_porosidade) on internal nodes.
        
        Args:
            flow: Estimated flow tensor [Batch, Num_Nodes, 1] or [Batch, Num_Nodes]
            edge_index: Graph connectivity [2, Num_Edges]
            edge_flow: Optional direct edge flows [Batch, Num_Edges, 1]
            edge_weight: Optional edge transition weights
            boundary_mask: Optional boolean tensor [Num_Nodes] marking perimeter boundary nodes
            boundary_tolerance: Optional tolerance margin for boundary imbalances (None = exempt)
            permeability_slack: Optional slack threshold for internal origins/destinations
        Returns:
            loss_spatial_conservation: Mean Kirchhoff divergence error across valid junctions.
        """
        device = flow.device
        
        if edge_index is None or edge_index.numel() == 0:
            return torch.tensor(0.0, device=device)
            
        if flow.dim() == 1:
            flow = flow.unsqueeze(0).unsqueeze(-1)
        elif flow.dim() == 2:
            flow = flow.unsqueeze(-1)

        batch_size = flow.size(0)
        num_nodes = flow.size(1)

        src = edge_index[0].to(device)
        dst = edge_index[1].to(device)

        # 1. Edge flows along directed roads
        q_edges = self.compute_edge_flow(flow, edge_index, edge_flow, edge_weight, num_nodes=num_nodes)

        # 2. Inflow and Outflow per junction node
        inflow = torch.zeros(batch_size, num_nodes, 1, dtype=q_edges.dtype, device=device)
        outflow = torch.zeros(batch_size, num_nodes, 1, dtype=q_edges.dtype, device=device)

        inflow.index_add_(1, dst, q_edges)
        outflow.index_add_(1, src, q_edges)

        # Kirchhoff divergence |Sigma_in - Sigma_out| per junction
        div = torch.abs(inflow - outflow)

        # 3. Identify boundary nodes (entries: in_deg == 0, exits: out_deg == 0)
        in_deg = torch.zeros(num_nodes, device=device)
        out_deg = torch.zeros(num_nodes, device=device)
        in_deg.scatter_add_(0, dst, torch.ones_like(dst, dtype=torch.float))
        out_deg.scatter_add_(0, src, torch.ones_like(src, dtype=torch.float))

        is_source = (in_deg == 0)
        is_sink = (out_deg == 0)
        is_boundary = is_source | is_sink

        if boundary_mask is not None:
            is_boundary = is_boundary | boundary_mask.to(device)

        is_internal = ~is_boundary
        tol = boundary_tolerance if boundary_tolerance is not None else self.boundary_tolerance
        slack = permeability_slack if permeability_slack is not None else self.permeability_slack

        # Apply permeability slack on internal nodes: ReLU(|inflow - outflow| - slack)
        if slack > 0:
            div_internal = torch.relu(div[:, is_internal, :] - slack) if is_internal.any() else torch.empty(0, device=device)
        else:
            div_internal = div[:, is_internal, :] if is_internal.any() else torch.empty(0, device=device)

        # 4. Apply conservation loss with boundary tolerance
        if tol is None:
            # Boundary nodes are completely exempted from Kirchhoff penalty
            if div_internal.numel() > 0:
                internal_loss = div_internal.mean()
            else:
                internal_loss = torch.tensor(0.0, device=device)
            return self.penalty_scale * internal_loss
        else:
            # Boundary nodes receive a tolerance threshold
            penalty_internal = div_internal
            penalty_boundary = torch.relu(div[:, is_boundary, :] - tol) if is_boundary.any() else torch.empty(0, device=device)

            total_penalty = 0.0
            count = 0
            if penalty_internal.numel() > 0:
                total_penalty = total_penalty + penalty_internal.sum()
                count = count + penalty_internal.numel()
            if penalty_boundary.numel() > 0:
                total_penalty = total_penalty + penalty_boundary.sum()
                count = count + penalty_boundary.numel()

            loss = total_penalty / max(count, 1)
            return self.penalty_scale * loss

    def compute_loss(self, flow: torch.Tensor, edge_index: Optional[torch.Tensor] = None, **kwargs) -> torch.Tensor:
        """Alias for compute_residual."""
        return self.compute_residual(flow, edge_index, **kwargs)

    def forward(self, flow: torch.Tensor, edge_index: Optional[torch.Tensor] = None, **kwargs) -> torch.Tensor:
        """Forward pass delegates to compute_residual."""
        return self.compute_residual(flow, edge_index, **kwargs)
