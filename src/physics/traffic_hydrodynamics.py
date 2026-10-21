# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Dict, Any, Tuple
from src.physics.constants import (
    DEFAULT_JAM_DENSITY_PER_LANE,
    SpeedConverter,
    flow_to_density,
)


class TrafficHydrodynamicEngine:
    """
    Single Responsibility: Solves continuous traffic hydrodynamics (LWR continuum theory,
    Greenshields speed-density relation, and spatial graph interpolation).
    Pure physics domain service with zero dependency on serialization or transport.
    """

    @staticmethod
    def greenshields_speed(density: float, k_jam: float, v_free: float) -> float:
        """Calculates expected speed via Greenshields model: v(k) = v_free * (1 - k / k_jam)."""
        return max(1.5, v_free * (1.0 - min(1.0, density / k_jam)))

    @classmethod
    def resolve_edge_state(
        cls,
        edge: Any,
        data: Dict[str, Any],
        k_jam: float = DEFAULT_JAM_DENSITY_PER_LANE,
    ) -> Tuple[float, float]:
        """
        Determines canonical density (veh/km/lane) and speed (m/s) for a network edge.
        If direct telemetry is present, decodes and converts units; otherwise,
        interpolates hydrodynamics from neighboring graph nodes.
        """
        edge_id = str(edge.id)
        v_free = getattr(edge, "max_speed", 13.89)

        if edge_id in data:
            metrics = data[edge_id]
            raw_d = float(metrics.get("density", metrics.get("value", 15.0)))
            raw_s = float(metrics.get("speed", v_free))

            unit = metrics.get("speed_unit") or metrics.get("unit")
            if unit:
                speed = SpeedConverter.to_ms(raw_s, unit=unit)
            else:
                speed = SpeedConverter.to_ms(raw_s, "km/h") if raw_s > 35.0 else raw_s

            if raw_d > k_jam:
                speed_kmh = SpeedConverter.to_kmh(speed, "m/s")
                v_free_kmh = SpeedConverter.to_kmh(v_free, "m/s")
                density = flow_to_density(
                    flow_veh_h=raw_d,
                    current_speed_kmh=speed_kmh,
                    v_free_kmh=v_free_kmh,
                    k_jam=k_jam,
                )
            else:
                density = raw_d

            if "physics" in metrics and "a" not in metrics["physics"]:
                v_phys = float(metrics["physics"].get("v", 0.0))
                if v_phys > 0.5:
                    v_unit = metrics["physics"].get("unit")
                    if v_unit:
                        speed = SpeedConverter.to_ms(v_phys, unit=v_unit)
                    else:
                        speed = v_phys if v_phys <= 35.0 else SpeedConverter.to_ms(v_phys, "km/h")
        else:
            density, speed = cls.interpolate_node_hydrodynamics(edge, data, k_jam, v_free)

        # Rigorous bounds
        density = min(k_jam, max(0.5, density))
        speed = max(1.0, min(v_free * 1.1, speed))
        return density, speed

    @classmethod
    def interpolate_node_hydrodynamics(
        cls,
        edge: Any,
        data: Dict[str, Any],
        k_jam: float,
        v_free: float,
    ) -> Tuple[float, float]:
        """Spatial Graph Interpolation: propagate hydrodynamics from connected nodes."""
        node_from = data.get(edge.from_node, {}) if edge.from_node else {}
        node_to = data.get(edge.to_node, {}) if edge.to_node else {}

        vals = []
        speeds = []
        v_f = 0.0
        v_t = 0.0
        if node_from:
            v_f = float(node_from.get("value", 0.0))
            if v_f > 0.0:
                vals.append(v_f)
            phys_f = node_from.get("physics", {})
            if isinstance(phys_f, dict) and "a" not in phys_f:
                spd_f = float(phys_f.get("v", 0.0))
                if spd_f > 0.5:
                    speeds.append(spd_f)

        if node_to:
            v_t = float(node_to.get("value", 0.0))
            if v_t > 0.0:
                vals.append(v_t)
            phys_t = node_to.get("physics", {})
            if isinstance(phys_t, dict) and "a" not in phys_t:
                spd_t = float(phys_t.get("v", 0.0))
                if spd_t > 0.5:
                    speeds.append(spd_t)

        is_runtime_snapshot = ("type" in node_from) or ("type" in node_to)

        if vals:
            if is_runtime_snapshot and v_f > 0.0 and v_t > 0.0:
                # Directional weighting: downstream junction (spillback) + upstream junction (inflow)
                avg_val = 0.45 * v_f + 0.55 * v_t
            else:
                avg_val = sum(vals) / len(vals)

            if avg_val > k_jam:
                v_ref_kmh = SpeedConverter.to_kmh(v_free, "m/s")
                density = flow_to_density(
                    flow_veh_h=avg_val,
                    current_speed_kmh=v_ref_kmh,
                    v_free_kmh=v_ref_kmh,
                    k_jam=k_jam,
                )
            else:
                density = max(0.5, avg_val)

            if is_runtime_snapshot:
                # Modulate by road hierarchy permeability and physical link geometry (length/lanes)
                edge_type = str(getattr(edge, "edge_type", "highway.residential")).lower()
                priority = int(getattr(edge, "priority", 1))
                length = float(getattr(edge, "length", 100.0))
                lanes = max(1, int(getattr(edge, "lanes", 1)))

                if any(k in edge_type for k in ("motorway", "trunk", "primary", "secondary")) or priority >= 10:
                    perm = 0.92
                elif "tertiary" in edge_type or priority >= 6:
                    perm = 0.78
                elif "unclassified" in edge_type or priority >= 4:
                    perm = 0.62
                else:
                    perm = 0.42

                # Length & lane impedance factor: longer links and multi-lane links distribute density differently
                geom_factor = (1.0 / (1.0 + 0.09 * (length / 100.0))) * (1.0 / (lanes ** 0.25))
                density = max(0.65, density * perm * geom_factor)
        else:
            density = 15.0

        if speeds:
            raw_spd = sum(speeds) / len(speeds)
            speed = raw_spd if raw_spd <= 35.0 else SpeedConverter.to_ms(raw_spd, "km/h")
        else:
            speed = cls.greenshields_speed(density, k_jam, v_free)

        return density, speed

    @classmethod
    def resolve_unmapped_source(
        cls,
        metrics: Dict[str, Any],
        k_jam: float = DEFAULT_JAM_DENSITY_PER_LANE,
    ) -> Tuple[float, float]:
        """Resolves density and speed for unmapped fallback sensors."""
        if "density" in metrics or "speed" in metrics:
            d = float(metrics.get("density", 15.0))
            s = float(metrics.get("speed", 13.89))
        else:
            d = float(metrics.get("value", 15.0))
            v = 0.0
            if "physics" in metrics:
                v = float(metrics["physics"].get("v", 0.0))
            s = v if v > 0.5 else 13.89

        density = min(k_jam, max(0.5, d))
        speed = max(1.0, min(25.0, s))
        return density, speed
