# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import random
import pytest
import torch
import numpy as np

from src.strategies.hybrid_dynamic_calibrator import HybridDynamicCalibrator
from src.strategies.deep_svdd_calibrator import DeepSVDDCalibrator
from src.pipeline.auditor_pipeline import AuditorPipeline


def test_hybrid_dynamic_calibrator_warmup():
    """Verifies that during warmup (first 25 samples), scores use fallback threshold and don't false alarm."""
    calibrator = HybridDynamicCalibrator(
        warmup_cycles=25,
        initial_fallback_floor=0.85,
    )

    # Initial state
    assert calibrator.current_threshold == 0.85

    # Feed 20 normal scores typical of DeepSVDD (0.60 to 0.72)
    for _ in range(20):
        score = random.uniform(0.62, 0.71)
        is_anom, thresh, meta = calibrator.evaluate(score)
        assert is_anom is False
        assert thresh >= 0.85

    # Should still be warming up
    metrics = calibrator.get_metrics()
    assert metrics["is_warmed_up"] is False
    assert metrics["total_processed"] == 20


def test_hybrid_dynamic_calibrator_adaptation_and_outlier_detection():
    """Verifies that after warmup, the threshold dynamically bounds the baseline and flags true outliers."""
    calibrator = HybridDynamicCalibrator(
        warmup_cycles=25,
        window_size=100,
        initial_fallback_floor=0.80,
    )

    # Feed 30 steady scores ~0.65 with std ~0.02
    np.random.seed(42)
    steady_scores = np.random.normal(loc=0.65, scale=0.02, size=50)

    for sc in steady_scores:
        is_anom, thresh, _ = calibrator.evaluate(float(sc))
        assert is_anom is False
        assert thresh >= 0.80

    metrics = calibrator.get_metrics()
    assert metrics["is_warmed_up"] is True
    # Dynamic threshold should adapt to something safe above 0.65 (e.g. >= 0.80)
    adapted_thresh = calibrator.current_threshold
    assert adapted_thresh >= 0.80

    # User's reported false positive score (0.6845) must NOT trigger anomaly!
    is_anom, thresh, _ = calibrator.evaluate(0.6845)
    assert is_anom is False
    assert 0.6845 < thresh

    # A real anomaly (e.g. 1.35) MUST trigger anomaly
    is_anom, thresh, _ = calibrator.evaluate(1.35)
    assert is_anom is True
    assert 1.35 > thresh


def test_hybrid_dynamic_calibrator_anti_poisoning():
    """Verifies that malicious or anomalous scores are rejected by the anti-poisoning filter and not learned."""
    calibrator = HybridDynamicCalibrator(
        warmup_cycles=25,
        window_size=50,
        initial_fallback_floor=0.85,
    )

    # Warmup with normal scores
    for _ in range(30):
        calibrator.evaluate(0.65)

    window_len_before = len(calibrator._history)
    thresh_before = calibrator.current_threshold

    # Inject extreme anomalous score (attack or catastrophic fault)
    is_anom, thresh, _ = calibrator.evaluate(3.50)
    assert is_anom is True

    # Anti-poisoning shield must NOT add 3.50 to the sliding window
    assert len(calibrator._history) == window_len_before
    assert 3.50 not in calibrator._history
    # The threshold must not be inflated by the malicious outlier
    assert calibrator.current_threshold == thresh_before


def test_deep_svdd_calibrator_delegation():
    """Verifies that DeepSVDDCalibrator delegates correctly to HybridDynamicCalibrator."""
    calibrator = DeepSVDDCalibrator(latent_dim=16)

    # Default fallback threshold floor should be >= 0.85
    assert calibrator.current_threshold >= 0.85

    # User score 0.6845 must evaluate as normal
    is_anom, thresh, _ = calibrator.evaluate(0.6845)
    assert is_anom is False
    assert thresh >= 0.85


def test_auditor_pipeline_end_to_end_no_false_alarm():
    """Verifies that AuditorPipeline processes normal scores without triggering emergency fallback."""
    pipeline = AuditorPipeline(
        latent_dim=16,
        persistence_threshold=7,
    )

    # Run cycles with normal synthetic input
    x = torch.randn(1, 60)
    for cycle in range(10):
        res = pipeline.audit(x)
        assert res["trigger_emergency_fallback"] is False
        assert res["threshold"] >= 0.85
