# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import logging
from typing import List, Optional, Any, Dict, Tuple
import numpy as np

from src.domain.entities import DataSource, MapEdge
from src.pipeline.global_polyline_extractor import (
    GlobalPolylineExtractor,
    extract_global_polyline,
)
from src.services.geo_projection_service import (
    GeoProjectionService,
    SumoLocationParams,
    get_projection_service_for_map,
    project_polyline_to_sumo,
)
from src.linguist.local_topology_matcher import LocalTopologyMatcher
from src.linguist.global_cartographer_matcher import GlobalCartographerMatcher
from src.linguist.compass_reconciler import CompassReconciler

logger = logging.getLogger("Synapse.Linguist.SpatialReconciler")


class SpatialReconciler:
    """
    Pure Orchestrator Architecture for Sensor Spatial Reconciliation.

    SOLID Compliance:
    - [SRP] Single Responsibility: Pure high-level orchestrator.
            Coordinates local topology discovery, global neural map-matching,
            and directional orientation reconciliation.
    - [OCP] Open for extension via pluggable matchers and reconcilers.
    - [DIP] Injects LocalTopologyMatcher, GlobalCartographerMatcher, and CompassReconciler.
    """

    def __init__(
        self,
        app_state: Any,
        local_matcher: Optional[LocalTopologyMatcher] = None,
        global_matcher: Optional[GlobalCartographerMatcher] = None,
        compass_reconciler: Optional[CompassReconciler] = None,
        polyline_extractor: Optional[GlobalPolylineExtractor] = None,
        projection_service: Optional[GeoProjectionService] = None,
    ):
        self.app_state = app_state
        self.local_matcher = local_matcher or LocalTopologyMatcher(app_state)
        self.global_matcher = global_matcher or GlobalCartographerMatcher(
            app_state=app_state,
            polyline_extractor=polyline_extractor,
            projection_service=projection_service,
        )
        self.compass_reconciler = compass_reconciler or CompassReconciler(app_state)

    def find_candidate_edges(
        self,
        source: DataSource,
        agent_factory: Optional[Any] = None,
        data_chunk: Optional[List[Any]] = None,
    ) -> List[MapEdge]:
        """
        Orchestrates candidate edge discovery.
        - Local sensors (is_local=True): delegates to LocalTopologyMatcher (fixed topology / metadata).
        - Global sensors (is_local=False): delegates to GlobalCartographerMatcher (neural map-matching).
        """
        if not self.app_state:
            return []

        # 1. Local sensors maintain direct topology and never invoke Cartographer
        if getattr(source, "is_local", True):
            if data_chunk is not None:
                return self.local_matcher.find_candidates(source, data_chunk=data_chunk)
            return self.local_matcher.find_candidates(source)

        # 2. Global sensors (TomTom, Waze) invoke Cartographer neural map-matching
        return self.global_matcher.match(
            source=source,
            agent_factory=agent_factory,
            data_chunk=data_chunk,
        )

    def reconcile_orientation(
        self,
        source: DataSource,
        candidate_edges: List[MapEdge],
        agent_factory: Any,
        data_chunk: Optional[List[Any]],
        data_np: np.ndarray,
        sem_type: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Orchestrates directional orientation reconciliation and graph association via CompassReconciler.
        """
        return self.compass_reconciler.reconcile(
            source=source,
            candidate_edges=candidate_edges,
            agent_factory=agent_factory,
            data_chunk=data_chunk,
            data_np=data_np,
            sem_type=sem_type,
        )
