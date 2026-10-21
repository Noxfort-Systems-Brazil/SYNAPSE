# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
IPC Data Transfer Object (DTO) Serializers (SOLID: SRP).

Encapsulates the transformation of domain entities and state into UI-ready payload structures.
"""

from typing import Dict, Any, List
from src.domain.app_state import AppState


class TopologySerializer:
    """Serializes road network topology into frontend React visualizer format."""

    @staticmethod
    def serialize_topology(app_state: AppState) -> Dict[str, Any]:
        """Serializes current map graph for the React visualizer."""
        try:
            nodes_list = []
            get_nodes_fn = getattr(app_state, "get_all_nodes", None)
            raw_nodes = get_nodes_fn() if callable(get_nodes_fn) else []
            for n in raw_nodes:
                nodes_list.append({
                    "id": n.id,
                    "x": n.x,
                    "y": n.y,
                    "name": getattr(n, "real_name", None),
                    "is_tls": getattr(n, "is_tls", bool(getattr(n, "tl_logic_id", False))),
                })

            edges_list = []
            get_edges_fn = getattr(app_state, "get_all_edges", None)
            raw_edges = get_edges_fn() if callable(get_edges_fn) else []
            for e in raw_edges:
                edges_list.append({
                    "id": e.id,
                    "from": e.from_node,
                    "to": e.to_node,
                    "name": getattr(e, "real_name", None),
                    "length": getattr(e, "length", 0.0),
                    "shape": getattr(e, "shape", []),
                })

            is_loaded = bool(nodes_list or edges_list)
            return {"nodes": nodes_list, "edges": edges_list, "loaded": is_loaded}
        except Exception as ex:
            return {"nodes": [], "edges": [], "loaded": False, "error": str(ex)}
