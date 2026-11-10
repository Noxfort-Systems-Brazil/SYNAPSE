# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from collections import deque
import logging
from typing import Dict, Any, Optional, Tuple
import numpy as np

from src.strategies.calibration.evt_pot_solver import EvtPotSolver
from src.strategies.calibration.tri_modal_ensemble import TriModalThresholdComputer

logger = logging.getLogger("Synapse.Strategies.HybridDynamicCalibrator")


class HybridDynamicCalibrator:
    """
    Tri-Modal Hybrid Adaptive Calibrator for Zero-Hardcoded Anomaly Detection.
    
    Orchestrates three complementary mathematical paradigms:
    1. Robust Statistics (Median + MAD scaled by 1.4826)
    2. Extreme Value Theory (EVT / Peaks-Over-Threshold - POT via GPD)
    3. Streaming Real-Time Tracking (Welford's Algorithm + EMA)
       
    Includes Anti-Poisoning Gate:
    Anomalous samples (attacks or sensor failures) are strictly blocked from contaminating
    the baseline distributions, preventing "frog-boiling" drift attacks.
    """

    def __init__(
        self,
        warmup_cycles: int = 25,
        window_size: int = 100,
        risk_p: float = 1e-3,
        k_sigmas: float = 3.0,
        ema_momentum: float = 0.05,
        initial_fallback_floor: float = 0.85,
    ):
        self.warmup_cycles = warmup_cycles
        self.window_size = window_size
        self.risk_p = risk_p
        self.k_sigmas = k_sigmas
        self.ema_momentum = ema_momentum
        self.initial_fallback_floor = initial_fallback_floor

        self._history: deque = deque(maxlen=window_size)
        self._cycle_count: int = 0
        self._ema_mean: Optional[float] = None
        self._ema_var: Optional[float] = None
        self._current_threshold: float = initial_fallback_floor
        self._is_warmed_up: bool = False

        # Diagnostic state
        self._last_t_robust: float = initial_fallback_floor
        self._last_t_evt: float = initial_fallback_floor
        self._last_t_stream: float = initial_fallback_floor

    @property
    def is_warmed_up(self) -> bool:
        return self._is_warmed_up

    @property
    def threshold(self) -> float:
        return self._current_threshold

    @threshold.setter
    def threshold(self, val: float) -> None:
        self._current_threshold = float(val)

    @property
    def current_threshold(self) -> float:
        return self._current_threshold

    def get_metrics(self) -> Dict[str, Any]:
        """Returns diagnostic metrics for monitoring and calibration inspection."""
        return {
            "current_threshold": self._current_threshold,
            "is_warmed_up": self._is_warmed_up,
            "total_processed": self._cycle_count,
            "history_size": len(self._history),
            "ema_mean": self._ema_mean,
            "ema_var": self._ema_var,
            "t_robust": self._last_t_robust,
            "t_evt": self._last_t_evt,
            "t_stream": self._last_t_stream,
        }

    def load_calibrated_state(self, threshold: float) -> None:
        """
        Initializes the calibrator directly in OPERATIONAL mode using an offline-calibrated threshold,
        eliminating redundant online warm-up cycles.
        """
        val = float(threshold)
        self._current_threshold = val
        self.initial_fallback_floor = val
        self._last_t_robust = val
        self._last_t_evt = val
        self._last_t_stream = val
        self._is_warmed_up = True
        self._cycle_count = max(self._cycle_count, self.warmup_cycles)

    def reset(self) -> None:
        """Resets dynamic tracking state after Fênix Hot-Reset or topology switch."""
        self._history.clear()
        self._cycle_count = 0
        self._ema_mean = None
        self._ema_var = None
        self._current_threshold = self.initial_fallback_floor
        self._is_warmed_up = False
        logger.info("[HybridDynamicCalibrator] Reset completed. Entering warm-up.")

    def evaluate(self, score: float) -> Tuple[bool, float, Dict[str, Any]]:
        """
        Evaluates an anomaly score against the dynamic ensemble threshold.
        Applies the Anti-Poisoning Gate: only legitimate traffic updates the models.
        """
        score = float(score)
        self._cycle_count += 1

        # --- Phase 1: Autonomous Warm-up ---
        if self._cycle_count <= self.warmup_cycles:
            self._history.append(score)
            self._update_ema(score)
            
            arr = np.array(self._history)
            p95 = float(np.percentile(arr, 95)) if len(arr) >= 5 else score * 1.35
            std_est = float(np.std(arr)) if len(arr) >= 5 else 0.1
            self._current_threshold = max(self.initial_fallback_floor, p95 + 2.0 * std_est)
            
            if self._cycle_count == self.warmup_cycles:
                self._is_warmed_up = True
                self._recalculate_ensemble_threshold()
                logger.info(
                    f"[HybridDynamicCalibrator] 🎓 Warm-up completed ({self.warmup_cycles} cycles). "
                    f"Dynamic threshold initialized at: {self._current_threshold:.4f}"
                )

            return False, self._current_threshold, {
                "phase": "WARM_UP",
                "cycle": self._cycle_count,
                "warmup_target": self.warmup_cycles,
                "t_robust": self._last_t_robust,
                "t_evt": self._last_t_evt,
                "t_stream": self._last_t_stream,
            }

        # --- Phase 2: Operational Inference & Threshold Comparison ---
        is_anomaly = score > self._current_threshold

        meta = {
            "phase": "OPERATIONAL",
            "cycle": self._cycle_count,
            "t_robust": self._last_t_robust,
            "t_evt": self._last_t_evt,
            "t_stream": self._last_t_stream,
            "ema_mean": self._ema_mean,
            "ema_std": np.sqrt(self._ema_var) if self._ema_var is not None else 0.0,
            "is_anomaly": is_anomaly,
        }

        # --- Phase 3: Anti-Poisoning Gate ---
        if not is_anomaly:
            self._history.append(score)
            self._update_ema(score)
            self._recalculate_ensemble_threshold()
        else:
            logger.warning(
                f"[HybridDynamicCalibrator] 🛡️ Anomaly detected: {score:.4f} > "
                f"{self._current_threshold:.4f}. Anti-poisoning active: baseline shielded."
            )

        return is_anomaly, self._current_threshold, meta

    def _update_ema(self, score: float) -> None:
        """Updates streaming mean and variance via Welford/EMA formulation."""
        if self._ema_mean is None or self._ema_var is None:
            self._ema_mean = score
            self._ema_var = 0.01
            return

        alpha = self.ema_momentum
        delta = score - self._ema_mean
        self._ema_mean += alpha * delta
        self._ema_var = (1.0 - alpha) * self._ema_var + alpha * (delta ** 2)

    def _recalculate_ensemble_threshold(self) -> None:
        """Computes consensus threshold across Robust, EVT, and Streaming pillars."""
        if len(self._history) < 10:
            return

        arr = np.array(self._history, dtype=np.float64)
        t_robust, t_evt, t_stream, consensus_threshold = TriModalThresholdComputer.compute_ensemble(
            history_arr=arr,
            k_sigmas=self.k_sigmas,
            risk_p=self.risk_p,
            initial_fallback_floor=self.initial_fallback_floor,
            ema_mean=self._ema_mean,
            ema_var=self._ema_var,
        )
        self._last_t_robust = t_robust
        self._last_t_evt = t_evt
        self._last_t_stream = t_stream
        self._current_threshold = consensus_threshold

    def _compute_evt_pot(self, arr: np.ndarray, median_val: float, sigma_mad: float) -> float:
        """Backward-compatible delegation to EvtPotSolver."""
        return EvtPotSolver.compute_evt_pot(
            arr=arr,
            median_val=median_val,
            sigma_mad=sigma_mad,
            risk_p=self.risk_p,
        )
