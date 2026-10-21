# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
import numpy as np

from src.physics.constants import (
    STANDARD_GRAVITY,
    GRAVITY,
    DEFAULT_VEHICLE_EFFECTIVE_LEN_M,
    DEFAULT_JAM_DENSITY_PER_LANE,
    DEFAULT_CAPACITY_PER_LANE_VEH_H,
    SATURATION_FLOW_RATE_PER_SEC,
    DEFAULT_URBAN_SPEED_LIMIT_KMH,
    MAX_URBAN_SPEED_CEILING_KMH,
    SpeedUnit,
    SpeedConverter,
    flow_to_density,
    occupancy_from_density,
    density_from_occupancy,
    calculate_camera_fov_capacity,
)
import src.kse.definitions as kse_defs
import src.physics.traffic_symbolic_rules as sym_rules
from src.engine.inference_engine import compute_telemetry_quality, DEFAULT_TELEMETRY_QUALITY_TAU


def test_standard_gravity_exact_value():
    """Verifies that gravity uses CGPM/ISO standard g0 = 9.80665 m/s^2 across all modules."""
    assert STANDARD_GRAVITY == 9.80665
    assert GRAVITY == 9.80665
    assert kse_defs.GRAVITY == 9.80665
    assert sym_rules.GRAVITY == 9.80665


def test_jam_density_and_effective_length_consistency():
    """Verifies physical consistency between effective vehicle length and jam density."""
    # 1000m / 140 veh ≈ 7.142857m per vehicle
    expected_density = 1000.0 / DEFAULT_VEHICLE_EFFECTIVE_LEN_M
    assert abs(DEFAULT_JAM_DENSITY_PER_LANE - expected_density) < 1e-4
    assert DEFAULT_JAM_DENSITY_PER_LANE == 140.0


def test_speed_converter_exact_factors():
    """Verifies that speed unit conversions use exact dimensional multipliers."""
    # 1 m/s = 3.6 km/h exactly
    assert SpeedConverter.to_kmh(1.0, "m/s") == pytest.approx(3.6, rel=1e-9)
    assert SpeedConverter.to_ms(3.6, "km/h") == pytest.approx(1.0, rel=1e-9)

    # 1 mph = 1.609344 km/h exactly
    assert SpeedConverter.to_kmh(100.0, "mph") == pytest.approx(160.9344, rel=1e-9)
    # 100 mph to m/s
    assert SpeedConverter.to_ms(100.0, "mph") == pytest.approx(160.9344 / 3.6, rel=1e-9)

    # Array conversions
    arr_ms = np.array([0.0, 10.0, 25.0])
    arr_kmh = SpeedConverter.to_kmh(arr_ms, "m/s")
    np.testing.assert_allclose(arr_kmh, [0.0, 36.0, 90.0])


def test_speed_unit_parser():
    """Verifies parsing of various unit strings to canonical SpeedUnit."""
    assert SpeedConverter.parse_unit("m/s") == SpeedUnit.MS
    assert SpeedConverter.parse_unit("mps") == SpeedUnit.MS
    assert SpeedConverter.parse_unit("meter/second") == SpeedUnit.MS
    assert SpeedConverter.parse_unit("mph") == SpeedUnit.MPH
    assert SpeedConverter.parse_unit("miles/hour") == SpeedUnit.MPH
    assert SpeedConverter.parse_unit("km/h") == SpeedUnit.KMH
    assert SpeedConverter.parse_unit(None) == SpeedUnit.KMH


def test_flow_to_density_hydrodynamics():
    """Verifies LWR hydrodynamic continuum relation q = k * v with Greenshields regularization."""
    # At free-flow speed 60 km/h and flow 1200 veh/h: k = 1200 / 60 = 20 veh/km
    k = flow_to_density(flow_veh_h=1200.0, current_speed_kmh=60.0, k_jam=140.0)
    assert k == pytest.approx(20.0, rel=1e-5)

    # At low speed (near-standstill, e.g. 1 km/h): regularization prevents infinite density and caps at k_jam
    k_standstill = flow_to_density(flow_veh_h=200.0, current_speed_kmh=1.0, v_free_kmh=60.0, k_jam=140.0)
    assert k_standstill <= 140.0
    assert k_standstill > 100.0

    # At complete stop (0.0 km/h): clipped safely to k_jam
    k_stopped = flow_to_density(flow_veh_h=0.0, current_speed_kmh=0.0, v_free_kmh=60.0, k_jam=140.0)
    assert 0.0 <= k_stopped <= 140.0


def test_occupancy_density_bidirectional_mapping():
    """Verifies clean occupancy <-> density mapping without artificial non-zero floors."""
    # Zero density -> exactly zero occupancy
    assert occupancy_from_density(0.0, k_jam=140.0) == 0.0
    assert density_from_occupancy(0.0, k_jam=140.0) == 0.0

    # Full jam density -> 1.0 occupancy
    assert occupancy_from_density(140.0, k_jam=140.0) == 1.0
    assert density_from_occupancy(1.0, k_jam=140.0) == 140.0

    # 50% occupancy -> 70 veh/km
    assert density_from_occupancy(0.5, k_jam=140.0) == 70.0
    assert occupancy_from_density(70.0, k_jam=140.0) == 0.5


def test_camera_fov_capacity():
    """Verifies optical capacity computation using geometry and vehicle effective length."""
    # 2 lanes, 45m depth, effective length ~7.142857m => 2 * (45 / 7.142857) = 2 * 6.3 = 12.6 vehicles
    cap = calculate_camera_fov_capacity(lanes=2, fov_depth_m=45.0)
    assert abs(cap - 12.6) < 0.1


def test_telemetry_quality_exponential_decay():
    """Verifies continuous, monotonic telemetry quality scoring."""
    # Perfect telemetry (loss = 0) => 100% quality
    assert compute_telemetry_quality(0.0) == 100

    # Baseline loss (0.008) with tau=0.08 => 100 * exp(-0.1) ≈ 90%
    q_baseline = compute_telemetry_quality(0.008)
    assert 89 <= q_baseline <= 91

    # High loss => degrades gracefully towards 10% floor without abrupt negative steps
    assert compute_telemetry_quality(0.08) == 37
    assert compute_telemetry_quality(0.5) == 10
