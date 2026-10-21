# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Tuple

# Enable Tensor Cores globally for matrix multiplications and cuDNN operations
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True

from src.utils.graph_utils import (
    compute_random_walk_transition_matrices,
    batch_offset_edge_index
)
from src.blocks.graph_blocks import (
    DiffusionGraphConv,
    AdaptiveAdjacency,
    ObservabilityGate,
    GatedTemporalConv
)

try:
    from torch_geometric.nn import GATv2Conv
    PYG_AVAILABLE = True
except ImportError:
    PYG_AVAILABLE = False
    GATv2Conv = None


class DiffusionGATv2(nn.Module):
    """
    Hybrid Spatio-Temporal Diffusion and Dynamic Attention Network.
    
    A pure neural model conforming to SOLID principles:
    1. Bidirectional Graph Diffusion (DiffusionGraphConv) for macroscopic flow spreading.
    2. Adaptive Node Embeddings (AdaptiveAdjacency) for latent topological correlation learning.
    3. GATv2 Dynamic Spatial Attention with observability masking.
    4. Sensor Observability Gating (ObservabilityGate) for calibrating ground truth anchors.
    """

    def __init__(
        self,
        num_nodes: int,
        in_channels: int = 32,
        hidden_channels: int = 64,
        out_channels: int = 32,
        diffusion_steps: int = 2,
        adaptive_dim: int = 16,
        gat_heads: int = 2,
        dropout: float = 0.1,
        damping_factor: float = 0.90,
        edge_dim: Optional[int] = 1
    ):
        super(DiffusionGATv2, self).__init__()
        self.num_nodes = num_nodes
        self.in_channels = in_channels
        self.hidden_channels = hidden_channels
        self.out_channels = out_channels
        self.diffusion_steps = diffusion_steps
        self.gat_heads = gat_heads
        self.damping_factor = damping_factor
        self.edge_dim = edge_dim
        
        # 1. Adaptive Graph Adjacency Block (SRP/DIP)
        self.adaptive_block = AdaptiveAdjacency(num_nodes=num_nodes, adaptive_dim=adaptive_dim)
        
        # 2. Dynamic Spatial Attention Layer (GATv2) runs FIRST to extract dynamic attention coefficients
        if PYG_AVAILABLE:
            head_dim = max(1, in_channels // gat_heads)
            self.gat_layer = GATv2Conv(
                in_channels=in_channels,
                out_channels=head_dim,
                heads=gat_heads,
                edge_dim=edge_dim,
                concat=True,
                dropout=dropout
            )
            self.gat_proj = nn.Linear(head_dim * gat_heads, in_channels) if (head_dim * gat_heads != in_channels) else nn.Identity()
        else:
            self.gat_layer = None
            self.gat_proj = nn.Identity()

        # 3. Layer Normalization & Dropout
        self.norm0 = nn.LayerNorm(in_channels)
        self.norm1 = nn.LayerNorm(hidden_channels)
        self.norm2 = nn.LayerNorm(out_channels)
        self.dropout = nn.Dropout(dropout)
        
        # 4. Diffusion Graph Convolution Blocks (SRP/DIP)
        self.diff_conv1 = DiffusionGraphConv(in_channels, hidden_channels, diffusion_steps)
        self.diff_conv2 = DiffusionGraphConv(hidden_channels, out_channels, diffusion_steps)
        
        # 5. Observability Gate Block (SRP/ISP)
        self.observability_gate = ObservabilityGate(in_channels=out_channels, out_channels=out_channels)

    def get_adaptive_adjacency(self) -> torch.Tensor:
        """
        Generates softmax-normalized adaptive adjacency matrix:
        A_adp = Softmax(ReLU(E1 * E2^T))
        """
        return self.adaptive_block()

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        observability_mask: Optional[torch.Tensor] = None,
        global_speed_factor: Optional[torch.Tensor] = None,
        edge_attr: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass.
        
        Args:
            x: Node features [Batch, Num_Nodes, In_Channels] or [Num_Nodes, In_Channels]
            edge_index: Graph connectivity [2, Num_Edges]
            observability_mask: Mask of active sensors [Num_Nodes] or [Batch, Num_Nodes, 1]
                                (1 = Ground Truth Sensor, 0 = Unobserved Virtual Node)
            global_speed_factor: Optional macroscopic speed weights for edges/nodes.
            edge_attr: Optional static edge attribute/conductance [Num_Edges, 1] derived from road hierarchy.
            
        Returns:
            extrapolated_embedding: [Batch, Num_Nodes, Out_Channels]
            adaptive_adj: Learned adjacency matrix [Num_Nodes, Num_Nodes]
        """
        # Ensure 3D batch dimension [Batch, Num_Nodes, In_Channels]
        if x.dim() == 2:
            x = x.unsqueeze(0)
            
        batch_size, num_nodes, in_dim = x.shape
        device = x.device
        
        # 1. Dynamic Attention Refinement & Learned Edge Attention Coefficients (GATv2)
        learned_edge_weights = None
        if self.gat_layer is not None and edge_index.numel() > 0 and edge_index.size(1) > 0:
            batch_edge_index = batch_offset_edge_index(edge_index, batch_size, num_nodes, device)
            
            # Prepare edge_attr for batched graph if provided
            batch_edge_attr = None
            if edge_attr is not None:
                ea = edge_attr.unsqueeze(-1) if edge_attr.dim() == 1 else edge_attr
                batch_edge_attr = ea.repeat(batch_size, 1).to(device) if batch_size > 1 else ea.to(device)
            elif global_speed_factor is not None and global_speed_factor.size(0) == edge_index.size(1):
                gf = global_speed_factor.unsqueeze(-1) if global_speed_factor.dim() == 1 else global_speed_factor
                batch_edge_attr = gf.repeat(batch_size, 1).to(device) if batch_size > 1 else gf.to(device)
            
            x_flat = x.view(-1, in_dim)
            try:
                gat_out, (edge_index_attn, alpha) = self.gat_layer(
                    x_flat,
                    batch_edge_index,
                    edge_attr=batch_edge_attr,
                    return_attention_weights=True
                )
                gat_out = self.gat_proj(gat_out)
                x_spatial = gat_out.view(batch_size, num_nodes, in_dim)
                x = self.norm0(x + self.dropout(F.elu(x_spatial)))
                
                # Extract learned attention weights for base edges (averaging across heads)
                num_base_edges = edge_index.size(1)
                alpha_mean = alpha.mean(dim=-1)
                if batch_size > 1:
                    total_batch_edges = batch_edge_index.size(1)
                    base_alphas = alpha_mean[:total_batch_edges].view(batch_size, num_base_edges)
                    learned_edge_weights = base_alphas.mean(dim=0)
                else:
                    learned_edge_weights = alpha_mean[:num_base_edges]
                    
                # Modulate by static road hierarchy conductance if provided
                if edge_attr is not None:
                    conductance = edge_attr.squeeze(-1).to(device)
                    learned_edge_weights = learned_edge_weights * conductance
            except Exception:
                pass
        
        # 2. Compute dynamic transition matrices with damping \gamma (absorption/sinks/sources)
        if learned_edge_weights is not None:
            edge_weights = F.relu(learned_edge_weights)
        elif global_speed_factor is not None and edge_index.numel() > 0 and global_speed_factor.size(0) == edge_index.size(1):
            edge_weights = F.relu(global_speed_factor)
        elif edge_attr is not None:
            edge_weights = F.relu(edge_attr.squeeze(-1).to(device))
        else:
            edge_weights = None
        
        p_forward, p_backward = compute_random_walk_transition_matrices(
            num_nodes=num_nodes,
            edge_index=edge_index,
            edge_weight=edge_weights,
            device=device,
            damping_factor=self.damping_factor
        )
        self.last_p_forward = p_forward.detach()
        self.last_p_backward = p_backward.detach()
        
        # 3. Adaptive Graph Adjacency
        adp_adj = self.adaptive_block().to(device)
        
        # 4. Bidirectional Diffusion Graph Convolutions
        h1 = self.diff_conv1(x, p_forward, p_backward, adaptive_adj=adp_adj)
        h1 = self.norm1(F.relu(h1))
        h1 = self.dropout(h1)
        
        h2 = self.diff_conv2(h1, p_forward, p_backward, adaptive_adj=adp_adj)
        h2 = self.norm2(F.relu(h2))
            
        # 5. Observability Gate (Dynamic Calibration & Anchor preservation)
        h2 = self.observability_gate(h=h2, x_raw=x, observability_mask=observability_mask)

        return h2, adp_adj


__all__ = [
    "DiffusionGATv2",
    "DiffusionGraphConv",
    "AdaptiveAdjacency",
    "ObservabilityGate",
    "GatedTemporalConv"
]
