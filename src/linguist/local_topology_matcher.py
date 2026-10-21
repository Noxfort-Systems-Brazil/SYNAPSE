# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import math
import logging
from typing import List, Optional, Any
from src.domain.entities import DataSource, MapEdge

logger = logging.getLogger("Synapse.Linguist.LocalTopologyMatcher")


class LocalTopologyMatcher:
    """
    Sub-component responsible for resolving topological candidates for local or pre-configured sensors.
    
    SOLID Compliance:
    - [SRP] Exclusively handles direct association lookups, metadata edge resolution,
            and local geometric proximity fallbacks without invoking neural matchers.
    """

    def __init__(self, app_state: Any):
        self.app_state = app_state

    def find_candidates(
        self,
        source: DataSource,
        data_chunk: Optional[List[Any]] = None,
    ) -> List[MapEdge]:
        """
        Locates candidate MapEdges for a local sensor.
        Checks associated element in app_state, metadata (edge_id, element_id, street_id),
        and falls back to geometric proximity if coordinates exist in metadata or data_chunk.
        """
        if not self.app_state:
            return []

        candidates: List[MapEdge] = []
        element_id = None

        # 1. Direct association in repository or app_state
        raw = self.app_state.get_element_for_source(source.id)
        if not isinstance(raw, str) and getattr(self.app_state, "sources", None) is not None:
            raw = self.app_state.sources.get_element_for_source(source.id)
        if isinstance(raw, str) and raw:
            element_id = raw

        # 2. Check metadata
        if not element_id and source.metadata:
            element_id = (
                source.metadata.get("edge_id")
                or source.metadata.get("element_id")
                or source.metadata.get("street_id")
                or source.metadata.get("road_id")
            )

        get_edge_fn = getattr(self.app_state, "get_edge", None)
        all_edges: List[MapEdge] = []
        try:
            all_edges = self.app_state.get_all_edges() or []
        except Exception:
            all_edges = []

        if element_id:
            primary_edge = None
            if get_edge_fn:
                try:
                    primary_edge = get_edge_fn(str(element_id))
                except Exception:
                    primary_edge = None
            if not primary_edge:
                for e in all_edges:
                    if getattr(e, "id", None) == str(element_id):
                        primary_edge = e
                        break

            if primary_edge:
                candidates.append(primary_edge)
                opp_id = f"-{primary_edge.id}" if not primary_edge.id.startswith("-") else primary_edge.id[1:]
                opp_edge = None
                if get_edge_fn:
                    try:
                        opp_edge = get_edge_fn(opp_id)
                    except Exception:
                        opp_edge = None
                if not opp_edge:
                    for e in all_edges:
                        if getattr(e, "id", None) == opp_id:
                            opp_edge = e
                            break
                        if (
                            getattr(e, "from_node", None) == primary_edge.to_node
                            and getattr(e, "to_node", None) == primary_edge.from_node
                            and getattr(e, "id", None) != primary_edge.id
                        ):
                            opp_edge = e
                            break
                if opp_edge and opp_edge.id not in [c.id for c in candidates]:
                    candidates.append(opp_edge)
                return candidates

        # 3. If element_id was a node or not an edge, check edges connected to it
        if element_id:
            for e in all_edges:
                if getattr(e, "from_node", None) == str(element_id) or getattr(e, "to_node", None) == str(element_id):
                    if e not in candidates:
                        candidates.append(e)
            if candidates:
                return candidates

        # 4. Local geometric proximity fallback (from metadata or data_chunk samples)
        pos_x = None
        pos_y = None
        if source.metadata:
            pos_x = source.metadata.get("x") or source.metadata.get("lon") or source.metadata.get("longitude")
            pos_y = source.metadata.get("y") or source.metadata.get("lat") or source.metadata.get("latitude")

        # If coordinates are missing from metadata, extract from data_chunk
        if (pos_x is None or pos_y is None) and data_chunk:
            try:
                from src.pipeline.global_polyline_extractor import GlobalPolylineExtractor
                extractor = GlobalPolylineExtractor()
                raw_pts = extractor.extract(data_chunk, source.metadata)
                if raw_pts and len(raw_pts) > 0:
                    pos_x, pos_y = raw_pts[0]
                    if not isinstance(source.metadata, dict):
                        source.metadata = {}
                    source.metadata["lon"] = pos_x
                    source.metadata["lat"] = pos_y
            except Exception as e:
                logger.debug(f"[LocalTopologyMatcher] Falha ao extrair coordenadas de data_chunk: {e}")

        if pos_x is not None and pos_y is not None and all_edges:
            try:
                px, py = float(pos_x), float(pos_y)

                # If coordinates are WGS84 GPS degrees, project to SUMO metric space
                if -180.0 <= px <= 180.0 and -90.0 <= py <= 90.0:
                    raw_map_path = self.app_state.get_map_source_path()
                    map_path = raw_map_path if isinstance(raw_map_path, str) else None
                    if not map_path and source.metadata:
                        map_path = source.metadata.get("map_file_path") or source.metadata.get("map_path")

                    from src.services.geo_projection_service import get_projection_service_for_map
                    proj_service = get_projection_service_for_map(map_path)
                    projected = proj_service.project([(px, py)])
                    if projected and len(projected) > 0:
                        px, py = projected[0]

                from src.utils.geometry import point_to_polyline_distance

                def edge_dist(e: MapEdge) -> float:
                    shape = getattr(e, "shape", None)
                    if shape:
                        d = point_to_polyline_distance(px, py, shape)
                        if math.isfinite(d):
                            return d
                        mx = sum(p[0] for p in shape) / len(shape)
                        my = sum(p[1] for p in shape) / len(shape)
                        return math.hypot(px - mx, py - my)
                    return float("inf")

                sorted_edges = sorted(all_edges, key=edge_dist)
                if sorted_edges:
                    closest = sorted_edges[0]
                    candidates.append(closest)
                    opp_id = f"-{closest.id}" if not closest.id.startswith("-") else closest.id[1:]
                    for e in all_edges:
                        if getattr(e, "id", None) == opp_id or (
                            getattr(e, "from_node", None) == closest.to_node
                            and getattr(e, "to_node", None) == closest.from_node
                            and getattr(e, "id", None) != closest.id
                        ):
                            candidates.append(e)
                            break

                    logger.info(
                        f"📍 [LocalTopologyMatcher] Sensor local '{source.name}' ({source.id}) "
                        f"associado geometricamente à via '{closest.id}' (candidatos: {[c.id for c in candidates]})."
                    )
                    return candidates
            except Exception as e:
                logger.debug(f"[LocalTopologyMatcher] Erro ao buscar edges locais por proximidade: {e}")

        return candidates
