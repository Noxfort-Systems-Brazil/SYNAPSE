# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Optional, Tuple
import numpy as np
import logging

from src.domain.entities import DataSource, MapEdge
from src.physics.constants import (
    STANDARD_GRAVITY,
    GRAVITY,
    DEFAULT_CAPACITY_PER_LANE_VEH_H,
    SATURATION_FLOW_RATE_PER_SEC,
    DEFAULT_JAM_DENSITY_PER_LANE,
    DEFAULT_URBAN_SPEED_LIMIT_KMH,
    MAX_URBAN_SPEED_CEILING_KMH,
    MAX_VEHICLE_ACCEL_MS2,
    SpeedConverter,
    calculate_camera_fov_capacity,
)

logger = logging.getLogger("Synapse.Physics.TrafficSymbolicRules")



class TrafficSymbolicRules:
    """Encapsulates traffic physical domain rules and invariant checks."""

    @staticmethod
    def check_dynamic_bounds(
        data_np: np.ndarray,
        sem_type: str,
        unit: str,
        lanes: int,
        edge: Optional[MapEdge],
        dt_sec: float,
        source: DataSource,
        max_physical_bound: float = 10000.0
    ) -> Tuple[bool, str]:
        """Calculates dynamic physical limits based on roadway capacity and modality."""
        sem_lower = sem_type.lower()
        max_val = float(np.max(data_np))

        # A. Speed Bounds (m/s, km/h, mph)
        if "speed" in sem_lower:
            if edge and isinstance(getattr(edge, "max_speed", None), (int, float)) and edge.max_speed > 0:
                edge_speed_kmh = edge.max_speed * 3.6
            else:
                edge_speed_kmh = float(source.metadata.get("max_speed_kmh", DEFAULT_URBAN_SPEED_LIMIT_KMH))

            speed_ceiling_kmh = min(MAX_URBAN_SPEED_CEILING_KMH, max(edge_speed_kmh * 1.35, 40.0))

            if unit.lower() in ["m/s", "mps"]:
                bound = speed_ceiling_kmh / 3.6
                desc = f"{bound:.1f} m/s ({speed_ceiling_kmh:.0f} km/h)"
            elif unit.lower() in ["mph"]:
                bound = speed_ceiling_kmh / 1.60934
                desc = f"{bound:.1f} mph"
            else:
                bound = speed_ceiling_kmh
                desc = f"{bound:.1f} km/h"

            return (max_val <= bound), desc

        # B. Flow Bounds (veh/h, veh/min, veh/s)
        if "flow" in sem_lower or "fluxo" in sem_lower:
            capacity_veh_h = lanes * DEFAULT_CAPACITY_PER_LANE_VEH_H * 1.25
            if unit.lower() in ["veh/min", "veic/min", "vpm"]:
                bound = capacity_veh_h / 60.0
                desc = f"{bound:.1f} veh/min"
            elif unit.lower() in ["veh/s", "veic/s", "vps"]:
                bound = capacity_veh_h / 3600.0
                desc = f"{bound:.2f} veh/s"
            else:
                bound = capacity_veh_h
                desc = f"{bound:.0f} veh/h"

            return (max_val <= bound), desc

        # C. Count Bounds (discrete detections in time window dt)
        if "count" in sem_lower or "veic" in sem_lower or "contagem" in sem_lower:
            fov_depth = source.metadata.get("fov_depth_m") if (source and source.metadata) else None
            fov_capacity = calculate_camera_fov_capacity(lanes, fov_depth)
            throughput_capacity = lanes * SATURATION_FLOW_RATE_PER_SEC * max(dt_sec, 1.0) * 1.5
            bound = max(fov_capacity, fov_capacity + throughput_capacity)
            desc = f"{bound:.0f} veic (em dt={dt_sec:.1f}s)"
            return (max_val <= bound), desc

        # D. Density & Occupancy
        if "density" in sem_lower or "densidade" in sem_lower:
            bound = lanes * DEFAULT_JAM_DENSITY_PER_LANE
            desc = f"{bound:.0f} veh/km"
            return (max_val <= bound), desc

        if "occupancy" in sem_lower or "ocupacao" in sem_lower:
            bound = 100.0 if max_val > 1.0 else 1.0
            desc = f"{bound:.0f}%"
            return (max_val <= bound), desc

        # E. Generic Modality Fallback
        return (max_val <= max_physical_bound), f"{max_physical_bound}"

    @staticmethod
    def check_kinematic_acceleration(
        data_np: np.ndarray,
        unit: str,
        dt_sec: float,
        source_name: str
    ) -> bool:
        """Verifies if acceleration/deceleration between consecutive points is physically plausible."""
        speeds_ms = SpeedConverter.to_ms(data_np, unit)

        accels = np.abs(np.diff(speeds_ms)) / max(dt_sec, 0.1)
        max_accel = float(np.max(accels))

        if max_accel > MAX_VEHICLE_ACCEL_MS2:
            logger.warning(
                f"⚠️ [Physics] Violação Cinemática: Aceleração/frenagem impossível ({max_accel:.2f} m/s²) "
                f"detectada em '{source_name}' (Máximo tolerado: {MAX_VEHICLE_ACCEL_MS2} m/s²)."
            )
            return False

        return True

    @staticmethod
    def check_sensor_liveness(
        data_np: np.ndarray,
        sem_lower: str,
        source_name: str
    ) -> bool:
        """Verifies if sensor is truly active or dead flatline."""
        if len(data_np) < 10:
            return True

        if "count" in sem_lower or "dens" in sem_lower:
            return True

        if len(data_np) >= 20 and np.var(data_np) == 0.0 and np.mean(data_np) > 0.0:
            logger.warning(
                f"⚠️ [Physics] Violação: Sensor travado com valor estático contínuo ({np.mean(data_np):.2f}) "
                f"em '{source_name}'."
            )
            return False

        return True
