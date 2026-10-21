# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: src/managers/graph/hydrodynamics_engine.py
# Description: Pure hydrodynamic physics calculator for traffic edges (SOLID: SRP).

from typing import Tuple, Optional
from src.physics.constants import DEFAULT_JAM_DENSITY_PER_LANE, SpeedConverter, flow_to_density
from src.domain.entities import MapEdge


class EdgeHydrodynamicsEngine:
    """Calculates hydrodynamic state (speed, density) on traffic edges using Greenshields model."""

    @staticmethod
    def compute_edge_kinetics(
        target_edge: MapEdge,
        val: float,
        is_speed_sensor: bool,
        is_flow_sensor: bool,
        is_count_sensor: bool,
        measured_speed_ms: Optional[float] = None
    ) -> Tuple[float, float]:
        v_free = getattr(target_edge, "max_speed", 13.89)
        edge_len = getattr(target_edge, "length", 100.0)
        edge_lanes = getattr(target_edge, "lanes", 1)
        k_jam = DEFAULT_JAM_DENSITY_PER_LANE

        if is_speed_sensor:
            speed_val = max(1.0, min(v_free * 1.1, val))
            speed_ratio = min(1.0, speed_val / max(1.0, v_free))
            density_val = max(0.5, min(k_jam, k_jam * (1.0 - speed_ratio)))
        elif is_flow_sensor:
            flow_veh_h = val * 3600.0
            v_free_kmh = SpeedConverter.to_kmh(v_free, "m/s")
            if measured_speed_ms is not None and measured_speed_ms > 0.5:
                speed_val = max(1.0, min(v_free * 1.1, measured_speed_ms))
                curr_speed_kmh = SpeedConverter.to_kmh(speed_val, "m/s")
                density_from_flow = flow_to_density(
                    flow_veh_h=flow_veh_h,
                    current_speed_kmh=curr_speed_kmh,
                    v_free_kmh=v_free_kmh,
                    k_jam=k_jam
                )
                speed_ratio = min(1.0, speed_val / max(1.0, v_free))
                density_from_speed = k_jam * (1.0 - speed_ratio)
                density_val = max(0.5, min(k_jam, max(density_from_flow, density_from_speed)))
            else:
                density_val = max(0.5, min(k_jam, flow_to_density(
                    flow_veh_h=flow_veh_h,
                    current_speed_kmh=v_free_kmh,
                    v_free_kmh=v_free_kmh,
                    k_jam=k_jam
                )))
                speed_val = max(1.0, v_free * (1.0 - (density_val / k_jam)))
        elif is_count_sensor:
            eff_len_km = max(0.01, (edge_len * edge_lanes) / 1000.0)
            density_val = max(0.5, min(k_jam, val / eff_len_km))

            if measured_speed_ms is not None and measured_speed_ms > 0.5:
                speed_val = max(1.0, min(v_free * 1.1, measured_speed_ms))
                speed_ratio = min(1.0, speed_val / max(1.0, v_free))
                density_from_speed = k_jam * (1.0 - speed_ratio)
                density_val = max(density_val, density_from_speed)
            else:
                speed_val = max(1.0, v_free * (1.0 - (density_val / k_jam)))
        else:
            if val <= 0.0:
                density_val = 0.5
                speed_val = v_free
            elif val > 3.0:
                speed_val = max(1.0, min(v_free * 1.1, val))
                speed_ratio = min(1.0, speed_val / max(1.0, v_free))
                density_val = max(0.5, min(k_jam, k_jam * (1.0 - speed_ratio)))
            else:
                density_val = max(0.5, min(k_jam, val * 10.0))
                speed_val = max(1.0, v_free * (1.0 - (density_val / k_jam)))

        return float(speed_val), float(density_val)
