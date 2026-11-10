# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Tuple, Optional
import numpy as np

from src.strategies.calibration.evt_pot_solver import EvtPotSolver


class TriModalThresholdComputer:
    """
    Computes consensus thresholds across three statistical pillars:
    1. Robust Statistics (Median + MAD * 1.4826)
    2. Extreme Value Theory (EVT POT via GPD)
    3. Streaming Adaptative (EMA + Welford variance)
    """

    @classmethod
    def compute_ensemble(
        cls,
        history_arr: np.ndarray,
        k_sigmas: float,
        risk_p: float,
        initial_fallback_floor: float,
        ema_mean: Optional[float],
        ema_var: Optional[float],
    ) -> Tuple[float, float, float, float]:
        """
        Calculates individual pillar thresholds and the fused consensus threshold.
        Returns:
            (t_robust, t_evt, t_stream, current_threshold)
        """
        arr = np.ascontiguousarray(history_arr, dtype=np.float64)

        # ── PILLAR 1: Robust Statistics (Median + MAD) ──
        median_val = float(np.median(arr))
        mad = float(np.median(np.abs(arr - median_val)))
        sigma_mad = mad * 1.4826  # Standard normal scale factor
        t_robust = max(initial_fallback_floor, median_val + (k_sigmas * sigma_mad))

        # ── PILLAR 2: Extreme Value Theory (EVT / POT) ──
        raw_t_evt = EvtPotSolver.compute_evt_pot(
            arr=arr,
            median_val=median_val,
            sigma_mad=sigma_mad,
            risk_p=risk_p,
        )
        t_evt = max(initial_fallback_floor, raw_t_evt)

        # ── PILLAR 3: Adaptive Streaming (EMA + Welford) ──
        if ema_mean is not None and ema_var is not None:
            ema_std = float(np.sqrt(max(1e-6, ema_var)))
            t_stream = ema_mean + (k_sigmas * ema_std)
        else:
            t_stream = t_robust
        t_stream = max(initial_fallback_floor, t_stream)

        # ── CONSENSUAL FUSION (Weighted Envelope) ──
        # 40% EVT (extreme tail) + 30% Robust + 30% Streaming
        consensus = (
            0.40 * t_evt +
            0.30 * t_robust +
            0.30 * t_stream
        )

        # Conservative lower envelope floor: threshold never drops below robust spread
        fused_threshold = max(t_robust * 0.95, consensus)

        return t_robust, t_evt, t_stream, fused_threshold
