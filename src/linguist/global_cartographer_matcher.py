# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import logging
from typing import List, Optional, Any
from src.domain.entities import DataSource, MapEdge
from src.pipeline.global_polyline_extractor import GlobalPolylineExtractor
from src.services.geo_projection_service import (
    GeoProjectionService,
    get_projection_service_for_map,
)

from src.services.fast_map_matcher import FastMapMatcher

logger = logging.getLogger("Synapse.Linguist.GlobalCartographerMatcher")


class GlobalCartographerMatcher:
    """
    Sub-component responsible for geometric map-matching of global sensors (TomTom, Waze)
    against the SUMO network via FastMapMatcher (R-Tree / Fréchet).

    SOLID Compliance:
    - [SRP] Exclusively coordinates global sensor map-matching (extract polyline,
            project to SUMO metric space, execute geometric matching, and discover opposing edges).
    - [DIP] Injects GlobalPolylineExtractor, GeoProjectionService, and FastMapMatcher.
    """

    def __init__(
        self,
        app_state: Any,
        polyline_extractor: Optional[GlobalPolylineExtractor] = None,
        projection_service: Optional[GeoProjectionService] = None,
        map_matcher: Optional[FastMapMatcher] = None,
    ):
        self.app_state = app_state
        self.polyline_extractor = polyline_extractor or GlobalPolylineExtractor()
        self.projection_service = projection_service
        self.map_matcher = map_matcher

    def match(
        self,
        source: DataSource,
        agent_factory: Optional[Any] = None,
        data_chunk: Optional[List[Any]] = None,
    ) -> List[MapEdge]:
        """
        Executes deterministic map-matching for a global sensor.
        Requires 1 sample from data_chunk or coordinates from metadata.
        """
        candidates: List[MapEdge] = []
        if not self.app_state:
            return candidates

        raw_polyline = self.polyline_extractor.extract(data_chunk, source.metadata)
        if not raw_polyline:
            logger.warning(
                f"⚠️ [GlobalCartographerMatcher] Sensor global '{source.name}' ({source.id}) "
                f"sem coordenadas ou polilinha para Map Matching."
            )
            return candidates

        # Resolve projection service
        proj_service = self.projection_service
        if proj_service is None:
            raw_map_path = self.app_state.get_map_source_path()
            map_path = raw_map_path if isinstance(raw_map_path, str) else None
            if not map_path and source.metadata:
                map_path = source.metadata.get("map_file_path") or source.metadata.get("map_path")
            proj_service = get_projection_service_for_map(map_path)

        projected_polyline = proj_service.project(raw_polyline)
        logger.info(
            f"🗺️ [GlobalCartographerMatcher] Sensor global '{source.name}' polilinha extraída: "
            f"{len(raw_polyline)} pontos GPS -> projetados para SUMO."
        )

        get_edge_fn = getattr(self.app_state, "get_edge", None)
        all_edges: List[MapEdge] = []
        try:
            all_edges = self.app_state.get_all_edges() or []
        except Exception:
            all_edges = []

        try:
            # 1. Obtain deterministic matcher (injected or built over active edges)
            matcher = self.map_matcher
            matched_id = None
            confidence = 0.95
            method = "geometric_rtree"

            cartographer = (
                agent_factory.get_or_create_cartographer(source.id, app_state=self.app_state)
                if agent_factory is not None
                else None
            )
            match_res = None
            if cartographer is not None:
                if len(projected_polyline) >= 2:
                    match_res = cartographer.match_polyline(projected_polyline)
                elif len(projected_polyline) == 1:
                    match_res = cartographer.match_point(projected_polyline[0][0], projected_polyline[0][1])

            if isinstance(match_res, dict):
                matched_id = match_res.get("edge_id")
                confidence = match_res.get("confidence", 0.95)
                method = match_res.get("method", "geometric")
            else:
                if matcher is None and all_edges:
                    matcher = FastMapMatcher(all_edges)
                if matcher is not None:
                    if len(projected_polyline) >= 2:
                        res = matcher.match_polyline(projected_polyline)
                    elif len(projected_polyline) == 1:
                        res = matcher.match(projected_polyline[0][0], projected_polyline[0][1])
                    else:
                        res = None

                    if res and res.best_edge_id:
                        matched_id = res.best_edge_id
                        confidence = res.best_probability or 0.95
                        method = "geometric_rtree"

            if matched_id:
                matched_edge = None
                if get_edge_fn:
                    try:
                        matched_edge = get_edge_fn(matched_id)
                    except Exception:
                        matched_edge = None
                if not matched_edge:
                    for e in all_edges:
                        if getattr(e, "id", None) == matched_id:
                            matched_edge = e
                            break

                if matched_edge:
                    candidates.append(matched_edge)
                    opp_id = f"-{matched_edge.id}" if not matched_edge.id.startswith("-") else matched_edge.id[1:]
                    for e in all_edges:
                        if getattr(e, "id", None) == opp_id or (
                            getattr(e, "from_node", None) == matched_edge.to_node
                            and getattr(e, "to_node", None) == matched_edge.from_node
                            and getattr(e, "id", None) != matched_edge.id
                        ):
                            candidates.append(e)
                            break

                    # Save matched metadata
                    if source.metadata is not None:
                        source.metadata["sumo_polyline"] = projected_polyline
                        source.metadata["matched_edge_id"] = matched_id
                        source.metadata["map_matching_method"] = method
                        source.metadata["map_matching_confidence"] = confidence

                    logger.info(
                        f"🗺️ [GlobalCartographerMatcher] Mapeou sensor global '{source.name}' à via "
                        f"'{matched_id}' (confiança={confidence:.2%}, método={method})."
                    )
        except Exception as e:
            logger.warning(f"⚠️ [GlobalCartographerMatcher] Erro ao executar Map Matching para '{source.name}': {e}")
        finally:
            if agent_factory is not None:
                agent_factory.release_cartographer(source.id)

        return candidates

