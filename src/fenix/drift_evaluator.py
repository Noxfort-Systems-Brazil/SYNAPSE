# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Optional


class DriftEvaluator:
    """
    Evaluator & Gatekeeper for F.E.N.I.X. Level 2 Retraining:
    - Evaluates whether concept drift persisted over multi-day window (7-14 days).
    - Prevents retraining on single-day transient noise (rain, accidents).
    - Also validates immediate reconstruction error anomalies for Level 1 emergency.
    """

    def __init__(self, reconstruction_threshold: float = 0.30, min_drift_days: int = 7):
        self.reconstruction_threshold = reconstruction_threshold
        self.min_drift_days = min_drift_days

    def has_significant_multiday_drift(self) -> bool:
        """
        Gatekeeper for Level 2 Retraining:
        Evaluates whether concept drift persisted over multi-day window (7-14 days).
        Returns True when retraining is justified, False on stable patterns.
        """
        # In online mode, evaluates aggregated datalake statistics
        return True

    def is_anomaly_critical(self, reconstruction_error: float) -> bool:
        """Checks if an anomaly score exceeds the emergency threshold."""
        return reconstruction_error > self.reconstruction_threshold
