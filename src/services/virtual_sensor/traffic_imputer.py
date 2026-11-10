# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Dict, Tuple, List, Set, Any
from src.domain.entities import MapEdge, SourceStatus
from src.services.virtual_sensor.topology_neighbor_resolver import TopologyNeighborResolver


class VirtualTrafficImputer:
    """Calculates speed, flow and density in SI units for unobserved road edges."""

    @staticmethod
    def get_edge_measurements_si(edge: MapEdge, app_state: Any) -> Tuple[float, float]:
        """Reads latest physical speed (m/s) and flow (veh/s) from associated active sources."""
        sources = app_state.get_sources_associated_with_element(edge.id)
        speed_ms = getattr(edge, "max_speed", 13.89)
        flow_vps = 0.25 * getattr(edge, "lanes", 1)

        for sid in sources:
            src = app_state.get_data_source(sid)
            if src and src.status == SourceStatus.ACTIVE and src.latest_value is not None:
                val = float(src.latest_value)
                sem = (src.semantic_type or "").lower()
                unit = (src.inferred_unit or "").lower()

                if "speed" in sem or "vel" in sem:
                    if unit in ("km/h", "kmh"):
                        speed_ms = val / 3.6
                    elif unit == "mph":
                        speed_ms = val / 2.23694
                    else:
                        speed_ms = val
                elif "flow" in sem or "count" in sem or "fluxo" in sem:
                    if unit in ("veh/h", "veic/h"):
                        flow_vps = val / 3600.0
                    elif unit in ("veh/min", "veic/min"):
                        flow_vps = val / 60.0
                    else:
                        flow_vps = val

        return speed_ms, flow_vps

    @classmethod
    def impute_traffic_for_edge(
        cls,
        target_edge: MapEdge,
        all_edges: List[MapEdge],
        active_edge_ids: Set[str],
        app_state: Any
    ) -> Dict[str, Any]:
        """
        Computes deterministic SI speed (m/s) and flow (veh/s) for the unobserved edge
        using topological conservation rules or historical fallback.
        """
        nearest_info = TopologyNeighborResolver.find_nearest_active_edge(
            target_edge, all_edges, active_edge_ids
        )

        if nearest_info is not None:
            neighbor_edge, relation, _ = nearest_info
            speed_ms, flow_vps = cls.get_edge_measurements_si(neighbor_edge, app_state)

            target_lanes = max(1, getattr(target_edge, "lanes", 1))
            neighbor_lanes = max(1, getattr(neighbor_edge, "lanes", 1))
            lane_ratio = target_lanes / float(neighbor_lanes)

            imputed_flow = flow_vps * lane_ratio
            max_speed_ms = getattr(target_edge, "max_speed", 13.89)
            imputed_speed = min(speed_ms, max_speed_ms)
            density = imputed_flow / max(0.1, imputed_speed)

            return {
                "speed_ms": float(imputed_speed),
                "flow_vps": float(imputed_flow),
                "density_vpm": float(density),
                "method": f"neighbor_{relation}",
                "donor_edge_id": neighbor_edge.id
            }

        default_speed_ms = getattr(target_edge, "max_speed", 13.89) * 0.75
        target_lanes = max(1, getattr(target_edge, "lanes", 1))
        default_flow_vps = 0.20 * target_lanes
        density = default_flow_vps / max(0.1, default_speed_ms)

        return {
            "speed_ms": float(default_speed_ms),
            "flow_vps": float(default_flow_vps),
            "density_vpm": float(density),
            "method": "historical_baseline",
            "donor_edge_id": ""
        }
