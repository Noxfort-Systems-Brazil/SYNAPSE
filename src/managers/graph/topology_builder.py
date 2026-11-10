# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import List, Tuple
import torch

from src.domain.entities import MapNode, MapEdge


class GraphTopologyBuilder:
    """Builds graph connectivity representations and road-attribute tensors for GNN inference."""

    HIERARCHY_WEIGHTS = {
        "motorway": 1.0,
        "trunk": 1.0,
        "primary": 0.95,
        "secondary": 0.75,
        "tertiary": 0.50,
        "residential": 0.15,
        "living_street": 0.10,
        "service": 0.05,
        "unclassified": 0.20,
    }

    @classmethod
    def _compute_edge_conductance(cls, edge: MapEdge) -> float:
        """
        Calculates physical conductance of the road:
        Conductance = lanes * (max_speed / 13.89) * hierarchy_weight * (priority / 5.0)
        """
        raw_type = str(getattr(edge, "edge_type", "")).lower()
        matched_weight = 0.20  # default for unknown types
        for k, w in cls.HIERARCHY_WEIGHTS.items():
            if k in raw_type:
                matched_weight = w
                break

        lanes = max(1, getattr(edge, "lanes", 1))
        speed_factor = max(0.2, min(2.5, getattr(edge, "max_speed", 13.89) / 13.89))
        priority = max(1, min(15, getattr(edge, "priority", 1)))
        priority_factor = max(0.2, priority / 5.0)

        conductance = lanes * speed_factor * matched_weight * priority_factor
        return float(conductance)

    @classmethod
    def build_topology(
        cls,
        nodes: List[MapNode],
        edges: List[MapEdge],
        device: torch.device
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Constructs both Edge Index and Edge Attributes (Conductance / Road DNA) tensors.
        Returns:
            (edge_index: [2, Num_Edges], edge_attr: [Num_Edges])
        """
        id_map = {n.id: i for i, n in enumerate(nodes)}

        if not edges:
            return (
                torch.empty((2, 0), dtype=torch.long, device=device),
                torch.empty(0, dtype=torch.float, device=device)
            )

        edge_list = []
        attr_list = []
        for e in edges:
            if e.from_node in id_map and e.to_node in id_map:
                src_idx = id_map[e.from_node]
                dst_idx = id_map[e.to_node]
                edge_list.append([src_idx, dst_idx])
                attr_list.append(cls._compute_edge_conductance(e))

        if not edge_list:
            return (
                torch.empty((2, 0), dtype=torch.long, device=device),
                torch.empty(0, dtype=torch.float, device=device)
            )

        edge_index = torch.tensor(edge_list, dtype=torch.long, device=device).t().contiguous()
        edge_attr = torch.tensor(attr_list, dtype=torch.float, device=device)
        return edge_index, edge_attr

    @classmethod
    def build_edge_index(
        cls,
        nodes: List[MapNode],
        edges: List[MapEdge],
        device: torch.device
    ) -> torch.Tensor:
        """Constructs the Edge Index tensor required by PyTorch Geometric."""
        edge_index, _ = cls.build_topology(nodes, edges, device)
        return edge_index

    @classmethod
    def build_edge_attr(
        cls,
        nodes: List[MapNode],
        edges: List[MapEdge],
        device: torch.device
    ) -> torch.Tensor:
        """Constructs the Edge Attributes tensor required by GATv2."""
        _, edge_attr = cls.build_topology(nodes, edges, device)
        return edge_attr
