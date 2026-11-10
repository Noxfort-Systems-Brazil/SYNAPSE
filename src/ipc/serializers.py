# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
IPC Data Transfer Object (DTO) Serializers (SOLID: SRP).

Encapsulates the transformation of domain entities and state into UI-ready payload structures.
"""

from typing import Dict, Any, Optional, Tuple
from src.domain.app_state import AppState


class TopologySerializer:
    """Serializes road network topology into frontend React visualizer format."""

    _cached_topology: Optional[Dict[str, Any]] = None
    _cached_signature: Optional[Tuple[Any, ...]] = None

    @classmethod
    def invalidate_cache(cls) -> None:
        """Clears cached road network topology DTO."""
        cls._cached_topology = None
        cls._cached_signature = None

    @classmethod
    def serialize_topology(cls, app_state: AppState) -> Dict[str, Any]:
        """Serializes current map graph for the React visualizer with O(1) cache hits."""
        try:
            get_nodes_fn = getattr(app_state, "get_all_nodes", None)
            raw_nodes = get_nodes_fn() if callable(get_nodes_fn) else []
            get_edges_fn = getattr(app_state, "get_all_edges", None)
            raw_edges = get_edges_fn() if callable(get_edges_fn) else []

            signature = (
                id(app_state),
                len(raw_nodes),
                len(raw_edges),
                getattr(raw_nodes[0], "id", None) if raw_nodes else None,
                getattr(raw_edges[0], "id", None) if raw_edges else None,
            )
            if cls._cached_topology is not None and cls._cached_signature == signature:
                return cls._cached_topology

            nodes_list = [
                {
                    "id": n.id,
                    "x": n.x,
                    "y": n.y,
                    "name": getattr(n, "real_name", None),
                    "is_tls": getattr(n, "is_tls", bool(getattr(n, "tl_logic_id", False))),
                }
                for n in raw_nodes
            ]
            edges_list = [
                {
                    "id": e.id,
                    "from": e.from_node,
                    "to": e.to_node,
                    "name": getattr(e, "real_name", None),
                    "length": getattr(e, "length", 0.0),
                    "shape": getattr(e, "shape", []),
                }
                for e in raw_edges
            ]

            is_loaded = bool(nodes_list or edges_list)
            result = {"nodes": nodes_list, "edges": edges_list, "loaded": is_loaded}
            if is_loaded:
                cls._cached_signature = signature
                cls._cached_topology = result
            return result
        except Exception as ex:
            return {"nodes": [], "edges": [], "loaded": False, "error": str(ex)}


class TelemetrySerializer:
    """Optimizes high-frequency 1 Hz telemetry payloads for IPC STDOUT streaming."""

    @staticmethod
    def slim_global_results(results: Any) -> Any:
        """
        Strips unused 32-dim NumPy 'embedding' arrays from 'sensor_snapshot' before JSON serialization,
        returning a shallow copy so internal Python/KSE listeners receive the untouched dict.
        """
        if not isinstance(results, dict) or "sensor_snapshot" not in results:
            return results
        raw_snap = results.get("sensor_snapshot")
        if not isinstance(raw_snap, dict) or not raw_snap:
            return results

        slim_snap: Dict[str, Any] = {}
        for node_id, entry in raw_snap.items():
            if isinstance(entry, dict) and "embedding" in entry:
                slim_snap[node_id] = {k: v for k, v in entry.items() if k != "embedding"}
            else:
                slim_snap[node_id] = entry

        slim_payload = dict(results)
        slim_payload["sensor_snapshot"] = slim_snap
        return slim_payload
