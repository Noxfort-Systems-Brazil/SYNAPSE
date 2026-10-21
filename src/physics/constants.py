# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Single Source of Truth (SSOT) for Physical Constants, Dimensions, and Traffic Mechanics.

Standards adhered to:
- CGPM / ISO 80000-3:2019 (Standard Gravity, Exact Unit Conversions)
- Highway Capacity Manual (HCM 2016 / 2022) (Saturation flow, Jam Density)
- Lighthill-Whitham-Richards (LWR) Continuum Kinematic Wave Equations
"""

from enum import Enum
from typing import Optional, Union
import numpy as np


# =============================================================================
# 1. UNIVERSAL PHYSICAL CONSTANTS (ISO 80000-3 / CGPM)
# =============================================================================

# Standard Acceleration of Gravity at Sea Level (45 deg latitude)
STANDARD_GRAVITY: float = 9.80665  # m/s^2 (Exact standard acceleration of gravity)
GRAVITY: float = STANDARD_GRAVITY  # Canonical alias for backwards compatibility


# =============================================================================
# 2. MACROSCOPIC TRAFFIC ENGINEERING INVARIANTS (HCM STANDARDS)
# =============================================================================

# Jam Density per lane: HCM benchmark standard (veh/km/lane)
DEFAULT_JAM_DENSITY_PER_LANE: float = 140.0  # veh/km/lane (HCM standard)

# Average effective vehicle space occupancy in jam conditions: L_eff = 1000m / k_jam
DEFAULT_VEHICLE_EFFECTIVE_LEN_M: float = 1000.0 / DEFAULT_JAM_DENSITY_PER_LANE  # ~7.142857 meters


# Capacity & Saturation Flow Rate per lane
DEFAULT_CAPACITY_PER_LANE_VEH_H: float = 2400.0  # Max saturation flow per lane (veh/h)
SATURATION_FLOW_RATE_PER_SEC: float = DEFAULT_CAPACITY_PER_LANE_VEH_H / 3600.0  # ~0.6667 veh/s/lane

# Speed & Kinematic Limits
DEFAULT_URBAN_SPEED_LIMIT_KMH: float = 60.0  # Baseline urban speed limit (km/h)
MAX_URBAN_SPEED_CEILING_KMH: float = 200.0   # Absolute road vehicle physical limit (km/h)
MAX_VEHICLE_ACCEL_MS2: float = 12.0          # Max physical emergency acceleration/braking (m/s^2)
TYPICAL_MAX_ACCEL_MS2: float = 4.5           # Typical comfortable vehicle acceleration (m/s^2)
TYPICAL_MAX_DECEL_MS2: float = -9.0          # Typical dry-road hard braking deceleration (m/s^2)


# =============================================================================
# 3. UNIT CONVERSIONS & CANONICAL SPEED CONVERTER
# =============================================================================

class SpeedUnit(str, Enum):
    """Canonical traffic speed units."""
    KMH = "km/h"
    MS = "m/s"
    MPH = "mph"


class SpeedConverter:
    """
    Exact, mathematically rigorous unit conversion for velocity and speed metrics.
    Replaces fragile magnitude-based heuristics (such as value <= 35.0).
    """

    # Exact conversion ratios to km/h:
    # 1 m/s = 3600s / 1000m = 3.6 km/h (exact)
    # 1 international mile = 1609.344 meters => 1 mph = 1.609344 km/h (exact)
    _TO_KMH_FACTORS = {
        SpeedUnit.KMH: 1.0,
        SpeedUnit.MS: 3.6,
        SpeedUnit.MPH: 1.609344,
    }

    @classmethod
    def parse_unit(cls, unit_str: Optional[str]) -> SpeedUnit:
        """Normalizes free-form unit strings to canonical SpeedUnit."""
        if not unit_str:
            return SpeedUnit.KMH
        u = str(unit_str).strip().lower()
        if u in ("m/s", "mps", "meter/second", "meters/second"):
            return SpeedUnit.MS
        if u in ("mph", "miles/hour", "mi/h"):
            return SpeedUnit.MPH
        return SpeedUnit.KMH

    @classmethod
    def to_kmh(cls, value: Union[float, int, np.ndarray], unit: Optional[str] = None) -> Union[float, np.ndarray]:
        """Converts speed value to km/h using explicit unit metadata."""
        parsed = cls.parse_unit(unit)
        factor = cls._TO_KMH_FACTORS[parsed]
        return value * factor

    @classmethod
    def to_ms(cls, value: Union[float, int, np.ndarray], unit: Optional[str] = None) -> Union[float, np.ndarray]:
        """Converts speed value to m/s using explicit unit metadata."""
        parsed = cls.parse_unit(unit)
        factor_to_kmh = cls._TO_KMH_FACTORS[parsed]
        return (value * factor_to_kmh) / 3.6


# =============================================================================
# 4. RIGOROUS TRAFFIC HYDRODYNAMICS & KINEMATIC RELATIONS
# =============================================================================

def flow_to_density(
    flow_veh_h: float,
    current_speed_kmh: float,
    v_free_kmh: float = DEFAULT_URBAN_SPEED_LIMIT_KMH,
    k_jam: float = DEFAULT_JAM_DENSITY_PER_LANE
) -> float:
    """
    Converts traffic flow (veh/h) to density (veh/km) using LWR continuum theory (q = k * v).
    Smoothly regularizes at v -> 0 using the Greenshields congested regime to prevent singularities.
    """
    effective_speed = max(float(current_speed_kmh), 0.5)
    k_hydro = float(flow_veh_h) / effective_speed

    # In near-standstill conditions (v < 5 km/h), apply Greenshields branch constraint:
    # v = v_free * (1 - k/k_jam) => k_congested = k_jam * (1 - v/v_free)
    if effective_speed < 5.0:
        v_free_safe = max(float(v_free_kmh), 10.0)
        k_congested = k_jam * (1.0 - (effective_speed / v_free_safe))
        resolved_k = max(k_hydro, k_congested)
    else:
        resolved_k = k_hydro

    return float(np.clip(resolved_k, 0.0, k_jam))


def occupancy_from_density(density: float, k_jam: float = DEFAULT_JAM_DENSITY_PER_LANE) -> float:
    """
    Maps spatial density (veh/km) to space-time occupancy [0.0, 1.0].
    Free of artificial non-zero floors (0 density maps to exactly 0.0 occupancy).
    """
    if k_jam <= 0:
        return 0.0
    return float(np.clip(float(density) / k_jam, 0.0, 1.0))


def density_from_occupancy(occupancy: float, k_jam: float = DEFAULT_JAM_DENSITY_PER_LANE) -> float:
    """
    Maps space-time occupancy [0.0, 1.0] to physical vehicle density (veh/km).
    Dimensionally consistent with sensor detection field dimensions.
    """
    return float(np.clip(float(occupancy) * k_jam, 0.0, k_jam))


def calculate_camera_fov_capacity(
    lanes: int,
    fov_depth_m: Optional[float] = None,
    effective_len_m: float = DEFAULT_VEHICLE_EFFECTIVE_LEN_M
) -> float:
    """
    Calculates optical vehicle capacity within camera field-of-view (FOV)
    based on calibrated optical depth or urban default (45 meters).
    """
    depth = fov_depth_m if fov_depth_m is not None and fov_depth_m > 0 else 45.0
    safe_lanes = max(1, int(lanes))
    max_vehicles_per_lane = max(1.0, depth / max(effective_len_m, 1.0))
    return float(safe_lanes * max_vehicles_per_lane)
