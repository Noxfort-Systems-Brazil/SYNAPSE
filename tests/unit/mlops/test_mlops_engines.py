# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
import numpy as np
from src.mlops.loss_engine import LossEngine
from src.mlops.drift_engine import DriftEngine


def test_loss_engine_reconstruction():
    """Verifies that LossEngine computes normalized MSE accurately and safely."""
    # 1. Identical target and prediction
    target = np.array([10.0, 20.0, 30.0, 40.0], dtype=np.float32)
    loss_zero = LossEngine.compute_reconstruction_loss(target, target)
    assert loss_zero == pytest.approx(0.0, abs=1e-6)

    # 2. Known error
    pred = target + 5.0
    loss_val = LossEngine.compute_reconstruction_loss(target, pred)
    assert loss_val > 0.0

    # 3. None and empty handling
    assert LossEngine.compute_reconstruction_loss(None, target) == 0.0
    assert LossEngine.compute_reconstruction_loss(target, None) == 0.0
    assert LossEngine.compute_reconstruction_loss(np.array([]), np.array([])) == 0.0

    # 4. NaN / Inf tolerance
    target_dirty = np.array([10.0, np.nan, 30.0, np.inf], dtype=np.float32)
    pred_dirty = np.array([10.0, 50.0, 32.0, 100.0], dtype=np.float32)
    clean_loss = LossEngine.compute_reconstruction_loss(target_dirty, pred_dirty)
    assert np.isfinite(clean_loss)
    assert clean_loss >= 0.0


def test_loss_engine_hydrodynamic_residual():
    """Verifies conservation of mass: q = k * v."""
    speed = np.array([60.0, 40.0, 20.0], dtype=np.float32)      # km/h
    density = np.array([20.0, 30.0, 50.0], dtype=np.float32)    # veh/km
    flow = speed * density                                       # veh/h: [1200, 1200, 1000]

    # Exact physical flow -> residual must be 0
    res_zero = LossEngine.compute_hydrodynamic_residual(speed, density, flow)
    assert res_zero == pytest.approx(0.0, abs=1e-5)

    # Discrepant flow (e.g. sensor mismatch)
    corrupted_flow = flow * 1.5
    res_err = LossEngine.compute_hydrodynamic_residual(speed, density, corrupted_flow)
    assert res_err > 0.1

    # Edge cases
    assert LossEngine.compute_hydrodynamic_residual(None, density, flow) == 0.0


def test_drift_engine_psi_classification():
    """Verifies PSI calculation under Stable, Moderate Drift, and Critical Drift conditions."""
    drift_engine = DriftEngine(window_size=500, num_buckets=10, min_calibration_samples=100)

    # 1. Baseline calibration with Gaussian distribution centered at 50 km/h
    np.random.seed(42)
    baseline = np.random.normal(loc=50.0, scale=5.0, size=300)
    drift_engine.set_reference_data(baseline)
    assert drift_engine.is_ready is True

    # 2. Stable distribution (same mean and variance)
    stable_samples = np.random.normal(loc=50.0, scale=5.0, size=300)
    drift_engine.add_samples(stable_samples)
    metrics_stable = drift_engine.compute_metrics()

    assert metrics_stable["psi"] < 0.10
    assert metrics_stable["status_code"] == 0
    assert metrics_stable["status_message"] == "Stable"

    # 3. Moderate drift (shift mean by 1.5 km/h)
    drift_engine.reset()
    drift_engine.set_reference_data(baseline)
    moderate_samples = np.random.normal(loc=51.5, scale=5.0, size=300)
    drift_engine.add_samples(moderate_samples)
    metrics_moderate = drift_engine.compute_metrics()

    assert 0.10 <= metrics_moderate["psi"] < 0.25
    assert metrics_moderate["status_code"] == 1
    assert metrics_moderate["status_message"] == "Moderate Drift"

    # 4. Critical drift (severe congestion, mean drops to 30 km/h)
    drift_engine.reset()
    drift_engine.set_reference_data(baseline)
    critical_samples = np.random.normal(loc=30.0, scale=5.0, size=300)
    drift_engine.add_samples(critical_samples)
    metrics_critical = drift_engine.compute_metrics()

    assert metrics_critical["psi"] >= 0.25
    assert metrics_critical["status_code"] == 2
    assert metrics_critical["status_message"] == "Critical Drift"
