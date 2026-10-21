# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: src/managers/graph/element_resolver.py
# Description: Spatial element resolver binding sensors to nodes or edges (SOLID: SRP).

from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger("Synapse.ElementResolver")


class SensorElementResolver:
    """Resolves sensor affiliations to MapNodes or MapEdges with topological fallback."""

    @staticmethod
    def resolve_source_elements(
        source_id: str,
        app_state: Any,
        nodes: Dict[str, Any],
        meta: Dict[str, Any],
        raw_payload: Any = None
    ) -> List[str]:
        element_ids: List[str] = []
        sources_mgr = getattr(app_state, "sources", None)

        get_elems_fn = getattr(app_state, "get_elements_for_source", None) or getattr(
            sources_mgr, "get_elements_for_source", None
        )
        if callable(get_elems_fn):
            res = get_elems_fn(source_id)
            if isinstance(res, list):
                element_ids = res

        if not element_ids:
            get_elem_fn = getattr(app_state, "get_element_for_source", None) or getattr(
                sources_mgr, "get_element_for_source", None
            )
            single = get_elem_fn(source_id) if callable(get_elem_fn) else None
            if isinstance(single, str) and single:
                element_ids = [single]
            else:
                element_ids = [source_id]

        # Check whether source is local before performing fallback static associations
        src_obj = None
        get_src_fn = getattr(app_state, "get_data_source", None)
        if callable(get_src_fn):
            src_obj = get_src_fn(source_id)
        if src_obj is None:
            get_all_fn = getattr(app_state, "get_all_data_sources", None)
            if callable(get_all_fn):
                for s in (get_all_fn() or []):
                    if getattr(s, "id", None) == source_id:
                        src_obj = s
                        break
        is_local = getattr(src_obj, "is_local", True) if src_obj else True

        # Fallback association: if element_id is just source_id and not in active nodes, check metadata or coordinates (local sources only)
        if is_local and element_ids == [source_id] and source_id not in nodes:
            meta_edge = meta.get("matched_edge_id") or meta.get("edge_id") or meta.get("element_id")
            if meta_edge:
                element_ids = [meta_edge]
                assoc_fn = getattr(sources_mgr, "associate", None)
                if callable(assoc_fn):
                    assoc_fn(source_id, meta_edge)
            else:
                pos_x = meta.get("lon") or meta.get("longitude") or meta.get("x")
                pos_y = meta.get("lat") or meta.get("latitude") or meta.get("y")
                if (pos_x is None or pos_y is None) and isinstance(raw_payload, dict):
                    pos_x = raw_payload.get("lon") or raw_payload.get("longitude") or raw_payload.get("x")
                    pos_y = raw_payload.get("lat") or raw_payload.get("latitude") or raw_payload.get("y")
                elif (pos_x is None or pos_y is None) and isinstance(raw_payload, list) and len(raw_payload) > 0:
                    first_item = raw_payload[0]
                    if isinstance(first_item, dict):
                        loc = first_item.get("location", first_item)
                        if isinstance(loc, dict):
                            pos_x = loc.get("lon") or loc.get("longitude") or loc.get("x")
                            pos_y = loc.get("lat") or loc.get("latitude") or loc.get("y")
                    elif isinstance(first_item, str) and "," in first_item:
                        parts = [p.strip() for p in first_item.split(",")]
                        if len(parts) >= 5:
                            try:
                                pos_y = float(parts[3])
                                pos_x = float(parts[4])
                            except (ValueError, TypeError):
                                pass

                get_edges_fn = getattr(app_state, "get_all_edges", None)
                if pos_x is not None and pos_y is not None and callable(get_edges_fn):
                    try:
                        px, py = float(pos_x), float(pos_y)
                        if -180.0 <= px <= 180.0 and -90.0 <= py <= 90.0:
                            get_map_fn = getattr(app_state, "get_map_source_path", None)
                            map_path = get_map_fn() if callable(get_map_fn) else None
                            from src.services.geo_projection_service import get_projection_service_for_map
                            proj = get_projection_service_for_map(map_path)
                            projected = proj.project([(px, py)])
                            if projected:
                                px, py = projected[0]
                        from src.utils.geometry import point_to_polyline_distance
                        all_e = get_edges_fn() or []
                        if all_e:
                            best_edge = min(
                                all_e,
                                key=lambda e: point_to_polyline_distance(px, py, e.shape) if getattr(e, "shape", None) else float("inf")
                            )
                            element_ids = [best_edge.id]
                            assoc_fn = getattr(sources_mgr, "associate", None)
                            if callable(assoc_fn):
                                assoc_fn(source_id, best_edge.id)
                            if isinstance(meta, dict):
                                meta["matched_edge_id"] = best_edge.id
                    except Exception as e:
                        logger.debug(f"[ElementResolver] Erro no fallback de proximidade para {source_id}: {e}")

        return element_ids

