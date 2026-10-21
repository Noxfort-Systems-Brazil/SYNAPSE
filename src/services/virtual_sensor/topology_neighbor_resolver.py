# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: src/services/virtual_sensor/topology_neighbor_resolver.py
# Description: Topological and spatial nearest neighbor resolver for SUMO network edges (SOLID: SRP).

import math
from typing import List, Optional, Set, Tuple
from src.domain.entities import MapEdge


class TopologyNeighborResolver:
    """Locates closest active edges using upstream, downstream, neighbor, or spatial Euclidean proximity."""

    @staticmethod
    def get_edge_midpoint(edge: MapEdge) -> Tuple[float, float]:
        """Calculates 2D center point of an edge geometry."""
        if edge.shape and len(edge.shape) >= 2:
            pts = edge.shape
            mid_idx = len(pts) // 2
            return pts[mid_idx]
        elif edge.shape and len(edge.shape) == 1:
            return edge.shape[0]
        return (0.0, 0.0)

    @classmethod
    def find_nearest_active_edge(
        cls,
        target_edge: MapEdge,
        all_edges: List[MapEdge],
        active_edge_ids: Set[str]
    ) -> Optional[Tuple[MapEdge, str, float]]:
        """
        Locates the closest active edge using topological graph connections first,
        falling back to Euclidean spatial distance between road segment midpoints.
        """
        if not active_edge_ids:
            return None

        edge_map = {e.id: e for e in all_edges}

        # 1. Immediate Upstream Check
        for e in all_edges:
            if e.id in active_edge_ids and e.to_node == target_edge.from_node:
                return (e, "upstream", getattr(e, "length", 50.0))

        # 2. Immediate Downstream Check
        for e in all_edges:
            if e.id in active_edge_ids and e.from_node == target_edge.to_node:
                return (e, "downstream", getattr(e, "length", 50.0))

        # 3. Same-Junction Neighbors
        for e in all_edges:
            if e.id in active_edge_ids and e.id != target_edge.id:
                if e.from_node == target_edge.from_node or e.to_node == target_edge.to_node:
                    return (e, "junction_neighbor", getattr(e, "length", 75.0))

        # 4. Spatial Euclidean Fallback
        target_mid = cls.get_edge_midpoint(target_edge)
        best_edge = None
        min_dist = float("inf")

        for e_id in active_edge_ids:
            candidate = edge_map.get(e_id)
            if candidate:
                cand_mid = cls.get_edge_midpoint(candidate)
                dist = math.hypot(target_mid[0] - cand_mid[0], target_mid[1] - cand_mid[1])
                if dist < min_dist:
                    min_dist = dist
                    best_edge = candidate

        if best_edge is not None:
            return (best_edge, "euclidean_nearest", min_dist)

        return None
