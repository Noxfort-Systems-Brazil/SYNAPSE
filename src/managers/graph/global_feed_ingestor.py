# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Global Feed Ingestor (SOLID: SRP & OCP).

Specialized subcomponent for GraphManager that unpacks multi-segment global feeds
(e.g., Waze jams lists with per-street polylines & speeds), handles geodetic projections,
invokes FastMapMatcher, and routes kinematics to target SUMO edges.
"""

from typing import Any, Dict, List, Optional, Tuple, Callable
from src.managers.graph.payload_extractor import ExtractedTelemetry
from src.physics.constants import SpeedConverter
from src.utils.logging_setup import get_logger

logger = get_logger("GlobalFeedIngestor")


class GlobalJamsFeedIngestor:
    """
    Decoupled ingestor for third-party multi-segment feeds (Waze, TomTom, etc.).
    Keeps GraphManager clean of specific provider JSON schemas and projection mechanics.
    """

    def __init__(self):
        self._fast_matcher: Optional[Any] = None
        self._geo_proj: Optional[Any] = None
        self._active_feed_edges: Dict[str, set] = {}

    def reset(self):
        """Resets cached matchers and projections when map topology rebuilds."""
        self._fast_matcher = None
        self._geo_proj = None
        self._active_feed_edges.clear()

    def ingest(
        self,
        source_id: str,
        source_obj: Any,
        jams: List[Any],
        app_state: Any,
        direct_edge_metrics: Dict[str, Any],
        update_edge_fn: Callable[[str, ExtractedTelemetry], None]
    ) -> bool:
        """
        Unpacks multi-segment global jam feeds onto their matched network edges.
        
        Args:
            source_id: Data source ID
            source_obj: Data source domain entity
            jams: List of jam dictionary items from the feed
            app_state: Application state
            direct_edge_metrics: Direct edge metrics dictionary from GraphManager
            update_edge_fn: Callback to update edge element kinetics
            
        Returns:
            True if any jams were successfully mapped and ingested, False otherwise.
        """
        get_edges_fn = getattr(app_state, "get_all_edges", None)
        all_edges = get_edges_fn() if callable(get_edges_fn) else []
        if not all_edges:
            return False

        try:
            if self._fast_matcher is None:
                from src.services.fast_map_matcher import FastMapMatcher
                self._fast_matcher = FastMapMatcher(all_edges)
            if self._geo_proj is None:
                from src.services.geo_projection_service import get_projection_service_for_map
                get_path_fn = getattr(app_state, "get_map_source_path", None)
                map_path = get_path_fn() if callable(get_path_fn) else None
                self._geo_proj = get_projection_service_for_map(map_path)
        except Exception as e:
            logger.debug(f"[GlobalFeedIngestor] Failed to initialize matcher for global jams feed: {e}")
            return False

        matched_edges: set = set()
        jam_speeds_ms: List[float] = []

        for jam in jams:
            if not isinstance(jam, dict):
                continue
            
            spd_ms = self._extract_speed_ms(jam)
            if spd_ms is None or spd_ms <= 0.0:
                continue

            line = jam.get("line", [])
            if not isinstance(line, list) or len(line) < 2:
                continue

            raw_pts = self._extract_raw_points(line)
            if len(raw_pts) < 2:
                continue

            if -180.0 <= raw_pts[0][0] <= 180.0 and -90.0 <= raw_pts[0][1] <= 90.0:
                sumo_pts = self._geo_proj.project(raw_pts)
            else:
                sumo_pts = raw_pts

            res = self._fast_matcher.match_polyline(sumo_pts, radius_m=200.0)
            if res.best_edge_id and res.candidates and res.candidates[0].distance <= 50.0:
                edge_id = res.best_edge_id
                jam_telemetry = ExtractedTelemetry(
                    value=spd_ms,
                    is_speed_sensor=True,
                    is_flow_sensor=False,
                    is_count_sensor=False,
                    measured_speed_ms=spd_ms
                )
                update_edge_fn(edge_id, jam_telemetry)
                matched_edges.add(edge_id)
                jam_speeds_ms.append(spd_ms)

        if not matched_edges:
            return False

        # Clear previously jammed edges from this feed that have now cleared
        prev_edges = self._active_feed_edges.get(source_id, set())
        for stale_edge in (prev_edges - matched_edges):
            direct_edge_metrics.pop(stale_edge, None)
        self._active_feed_edges[source_id] = matched_edges

        if jam_speeds_ms and source_obj is not None:
            try:
                source_obj.latest_value = float(sum(jam_speeds_ms) / len(jam_speeds_ms))
            except Exception:
                pass

        return True

    @staticmethod
    def _extract_speed_ms(jam: Dict[str, Any]) -> Optional[float]:
        """Extracts and normalizes speed into m/s from multiple provider key conventions."""
        if "speedKMH" in jam and jam["speedKMH"] is not None:
            try:
                return SpeedConverter.to_ms(float(jam["speedKMH"]), "km/h")
            except (ValueError, TypeError):
                return None
        elif "speed_kmh" in jam and jam["speed_kmh"] is not None:
            try:
                return SpeedConverter.to_ms(float(jam["speed_kmh"]), "km/h")
            except (ValueError, TypeError):
                return None
        elif "speed" in jam and jam["speed"] is not None:
            try:
                s = float(jam["speed"])
                return s if s <= 35.0 else SpeedConverter.to_ms(s, "km/h")
            except (ValueError, TypeError):
                return None
        return None

    @staticmethod
    def _extract_raw_points(line: List[Any]) -> List[Tuple[float, float]]:
        """Parses list of points whether given as dicts {'x', 'y'} or tuples/lists."""
        raw_pts: List[Tuple[float, float]] = []
        for pt in line:
            if isinstance(pt, dict) and "x" in pt and "y" in pt:
                try:
                    raw_pts.append((float(pt["x"]), float(pt["y"])))
                except (ValueError, TypeError):
                    pass
            elif isinstance(pt, (list, tuple)) and len(pt) >= 2:
                try:
                    raw_pts.append((float(pt[0]), float(pt[1])))
                except (ValueError, TypeError):
                    pass
        return raw_pts
