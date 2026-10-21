# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: tests/unit/test_queue_dynamics.py
# Author: Gabriel Moraes
# Date: 2026-09-28

import pytest
from src.physics.queue_dynamics import TrafficQueueCalculator
from src.physics.constants import DEFAULT_JAM_DENSITY_PER_LANE


def test_calculate_storage_capacity():
    """Verifies physical storage capacity calculation based on link geometry and lane count."""
    # 100 meters, 2 lanes, ~7.14m effective length
    cap_2lanes = TrafficQueueCalculator.calculate_storage_capacity(100.0, 2)
    assert cap_2lanes == 28

    # 50 meters, 1 lane
    cap_1lane = TrafficQueueCalculator.calculate_storage_capacity(50.0, 1)
    assert cap_1lane == 7

    # Edge cases
    assert TrafficQueueCalculator.calculate_storage_capacity(0.0, 1) == 1


def test_estimate_edge_queue_free_flow_uncontrolled():
    """Uncontrolled link with light traffic moving at free-flow speed should have zero queue."""
    queue = TrafficQueueCalculator.estimate_edge_queue(
        density=10.0,  # light traffic
        speed=13.89,   # full free-flow speed (50 km/h)
        v_free=13.89,
        max_capacity=28,
        signal_group_id=-1,
        is_controlled=False,
    )
    assert queue == 0


def test_estimate_edge_queue_signalized_approach_red_accumulation():
    """Controlled link (traffic light) with normal density should accumulate cyclic queue (Webster/HCM)."""
    # 25 veh/km on a 28-veh capacity link = ~5 vehicles present on link
    queue = TrafficQueueCalculator.estimate_edge_queue(
        density=25.0,
        speed=11.0,
        v_free=13.89,
        max_capacity=28,
        signal_group_id=-1,
        is_controlled=True,  # Signalized approach
    )
    # n_veh = (25/140) * 28 = 5.0 -> cyclic queue = 5.0 * 0.6 = 3.0
    assert queue >= 2
    assert queue <= 28


def test_estimate_edge_queue_severe_congestion_and_crawl_speed():
    """Heavy traffic and crawling speed (<= 3.0 m/s) should convert entire link vehicle count into queue."""
    # 70 veh/km (half jam density) on a 28-veh capacity link = 14 vehicles
    queue = TrafficQueueCalculator.estimate_edge_queue(
        density=70.0,
        speed=2.0,  # Crawl speed (7.2 km/h <= 3.0 m/s)
        v_free=13.89,
        max_capacity=28,
        is_controlled=False,
    )
    # n_veh = (70/140) * 28 = 14 vehicles
    assert queue == 14


def test_estimate_fallback_queue():
    """Unmapped/fallback sources should estimate non-zero queue under moderate density and low speed."""
    # Normal density and slow speed
    q1 = TrafficQueueCalculator.estimate_fallback_queue(density=25.0, speed=5.0)
    assert q1 >= 1

    # Heavy jam density and stopped
    q2 = TrafficQueueCalculator.estimate_fallback_queue(density=140.0, speed=0.5)
    assert q2 == 15

    # Completely clear road
    q3 = TrafficQueueCalculator.estimate_fallback_queue(density=0.0, speed=13.89)
    assert q3 == 0
