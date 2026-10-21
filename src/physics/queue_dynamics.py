# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Any
from src.physics.constants import (
    DEFAULT_JAM_DENSITY_PER_LANE,
    DEFAULT_VEHICLE_EFFECTIVE_LEN_M,
)


class TrafficQueueCalculator:
    """
    Single Responsibility: Calculates physical storage capacity and dynamic queue lengths
    for roadway links according to Highway Capacity Manual (HCM) formulations.
    Pure physics domain calculation.
    """

    @staticmethod
    def calculate_storage_capacity(
        edge_len: float,
        edge_lanes: int,
        veh_effective_len: float = DEFAULT_VEHICLE_EFFECTIVE_LEN_M,
    ) -> int:
        """Physical storage capacity of a specific road link (maximum vehicles)."""
        return max(1, int((edge_len / veh_effective_len) * edge_lanes))

    @classmethod
    def estimate_edge_queue(
        cls,
        density: float,
        speed: float,
        v_free: float,
        max_capacity: int,
        signal_group_id: int = -1,
        is_controlled: bool = False,
        k_jam: float = DEFAULT_JAM_DENSITY_PER_LANE,
    ) -> int:
        """
        Estimates queue length based on physical vehicle presence (HCM continuum),
        speed degradation (congestion queue), and signalized approach cyclic accumulation (Webster).
        """
        if max_capacity <= 0:
            return 0

        # Physical vehicle count currently occupying the link
        density_ratio = min(1.0, max(0.0, density / k_jam)) if k_jam > 0 else 0.0
        n_veh = density_ratio * max_capacity

        # Congestion queue: when speed degrades relative to free-flow speed
        # Speeds <= 4.0 m/s (~14.4 km/h) are fully in queue regime
        if speed <= 4.0:
            q_cong = n_veh
        elif v_free > 0:
            congestion_ratio = max(0.0, 1.0 - (speed / v_free))
            q_cong = congestion_ratio * n_veh
        else:
            q_cong = 0.0

        # Cyclic queue: vehicles accumulated during red phase at signalized/controlled junctions
        has_signal = (signal_group_id != -1) or is_controlled
        q_cyclic = 0.0
        if has_signal and n_veh >= 0.4:
            # Under standard urban signal cycles (split ~0.5), ~50-60% of link arrivals stop on red
            q_cyclic = max(1.0, n_veh * 0.6)

        estimated_queue = max(q_cong, q_cyclic)
        return min(max_capacity, max(0, int(round(estimated_queue))))

    @staticmethod
    def estimate_fallback_queue(
        density: float,
        speed: float,
        k_jam: float = DEFAULT_JAM_DENSITY_PER_LANE,
        nominal_speed: float = 13.89,
    ) -> int:
        """Heuristic queue estimation for unmapped fallback sources."""
        density_ratio = min(1.0, max(0.0, density / k_jam)) if k_jam > 0 else 0.0
        n_veh = density_ratio * 15.0  # nominal urban link capacity = 15 vehicles
        if speed <= 3.0:
            return int(round(n_veh))
        speed_factor = max(0.0, 1.0 - min(1.0, speed / nominal_speed)) if nominal_speed > 0 else 0.0
        return int(round(speed_factor * n_veh))
