# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import time
import numpy as np
from typing import Tuple, Dict, Any, Optional
from src.utils.logging_setup import logger


class GroundTruthRealigner:
    """
    Single Responsibility: Manages Ground Truth Reality Re-anchoring (SOLID SRP).
    
    Responsibilities:
    - Detects Cold-Start conditions to prevent gating against zero.
    - Detects sensor recovery / arrival of fresh real data after dead-reckoning intervals.
    - Re-anchors the kinetic state vector [p, v, a] and resets Kalman covariance gracefully.
    - Prevents false-positive outlier rejections upon ground-truth resumption.
    """

    def __init__(self, dead_reckoning_gap_threshold: float = 2.0, max_consecutive_misses: int = 3):
        self.gap_threshold = dead_reckoning_gap_threshold
        self.max_misses = max_consecutive_misses

    def should_realign(
        self,
        node_id: str,
        measurement: float,
        current_pred_p: float,
        dt_since_last_live: float,
        consecutive_misses: int,
        is_first_sample: bool = False,
        nominal_dt: Optional[float] = None
    ) -> bool:
        """
        Determines whether the incoming measurement is a Ground Truth injection requiring realignment.
        """
        if is_first_sample:
            return True

        if consecutive_misses >= self.max_misses:
            return True

        # Adaptive gap: scales to 3 missed sampling intervals when nominal_dt is provided, or uses gap_threshold
        effective_gap = max(3.0 * float(nominal_dt), self.gap_threshold) if (nominal_dt is not None and nominal_dt > 0) else self.gap_threshold
        if dt_since_last_live >= effective_gap:
            return True

        return False

    def realign(
        self,
        node_id: str,
        measurement: float,
        previous_p: float,
        dt: float,
        r_val: float
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Executes reality re-anchoring on the state vector and covariance matrix.
        
        Returns:
            (new_x: np.ndarray, new_P: np.ndarray, reality_delta: float)
        """
        z = float(measurement)
        prev = float(previous_p)
        clamped_dt = max(0.05, min(10.0, dt))

        # Velocity inferred from ground-truth jump, bounded by physical traffic limits (-30 to +30 m/s or veh/s)
        inferred_v = float(np.clip((z - prev) / clamped_dt, -30.0, 30.0))
        reality_delta = abs(z - prev)

        new_x = np.array([[z], [inferred_v], [0.0]], dtype=np.float64)

        # Reset covariance: Position is anchored to sensor noise R; V and A reset with moderate uncertainty
        new_P = np.array([
            [r_val, 0.0, 0.0],
            [0.0, max(10.0, r_val * 5.0), 0.0],
            [0.0, 0.0, max(20.0, r_val * 10.0)]
        ], dtype=np.float64)

        logger.info(
            f"[KSE] 🎯 Reality Anchor on Node {node_id}: Ground Truth={z:.2f} "
            f"(prev={prev:.2f}, delta={reality_delta:.2f}, dt={dt:.2f}s, v_init={inferred_v:.2f})"
        )

        return new_x, new_P, reality_delta
