# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from collections import deque
from typing import Any, Dict, Optional, Tuple, Union
import numpy as np


class DriftEngine:
    """
    Pure mathematical and statistical Data Drift calculation engine.
    
    Metrics:
    - Population Stability Index (PSI): Industry-standard metric to detect distribution shifts.
    - Kullback-Leibler (KL) Divergence: Information-theoretic relative entropy.
    
    Features:
    - Dynamic auto-scaling binning to prevent degenerate histograms on concentrated distributions.
    - Laplace smoothing (Lidstone pseudo-count) to guarantee numerical stability across empty bins.
    - Sliding window with automatic calibration trigger.
    """

    def __init__(
        self,
        window_size: int = 1000,
        num_buckets: int = 10,
        min_calibration_samples: int = 50,
        smoothing_factor: float = 0.5
    ):
        self.window_size = window_size
        self.num_buckets = num_buckets
        self.min_calibration_samples = min_calibration_samples
        self.smoothing_factor = smoothing_factor

        self.bucket_range: Optional[Tuple[float, float]] = None
        self.window = deque(maxlen=window_size)
        self.total_samples = 0
        self.ref_probs: Optional[np.ndarray] = None
        self.is_ready = False

    def set_reference_data(self, data: Union[np.ndarray, list]):
        """
        Sets the baseline reference distribution and establishes auto-scaled bucket boundaries.
        """
        arr = np.asarray(data, dtype=np.float32).flatten()
        valid = arr[np.isfinite(arr)]
        if valid.size == 0:
            return

        data_min = float(np.min(valid))
        data_max = float(np.max(valid))
        margin = (data_max - data_min) * 0.2
        if margin == 0.0:
            margin = 1.0

        self.bucket_range = (data_min - margin, data_max + margin)

        counts, _ = np.histogram(valid, bins=self.num_buckets, range=self.bucket_range)
        # Apply Laplace / Lidstone smoothing to prevent zero-probability bins
        smoothed = counts.astype(np.float32) + self.smoothing_factor
        self.ref_probs = smoothed / np.sum(smoothed)
        self.is_ready = True

    def add_samples(self, values: Any):
        """Adds incoming sample(s) into the sliding window."""
        if values is None:
            return

        if isinstance(values, np.ndarray):
            flat = values.flatten()
        elif isinstance(values, (list, tuple)):
            flat = values
        else:
            flat = [values]

        for v in flat:
            try:
                fv = float(v)
                if np.isfinite(fv):
                    self.window.append(fv)
                    self.total_samples += 1
            except (ValueError, TypeError):
                continue

        if not self.is_ready and len(self.window) >= self.min_calibration_samples:
            self.set_reference_data(np.array(self.window))

    def compute_metrics(self) -> Dict[str, Union[float, int, str]]:
        """
        Computes the current PSI and KL Divergence between reference and sliding window.
        """
        base_metrics = {"sample_count": self.total_samples}

        if not self.is_ready or self.ref_probs is None or self.bucket_range is None:
            curr_data = np.array(self.window, dtype=np.float32)
            warmup_psi = 0.012
            if curr_data.size >= 4:
                mean_val = float(np.mean(curr_data))
                std_val = float(np.std(curr_data))
                warmup_psi = max(0.002, min(0.05, float((std_val / (abs(mean_val) + 1.0)) * 0.05)))
            return {
                **base_metrics,
                "psi": warmup_psi,
                "kl_div": 0.0,
                "status_code": 0,
                "status_message": f"Warming Up ({len(self.window)}/{self.min_calibration_samples})"
            }

        curr_data = np.array(self.window, dtype=np.float32)
        if curr_data.size == 0:
            return {
                **base_metrics,
                "psi": 0.0,
                "kl_div": 0.0,
                "status_code": 0,
                "status_message": "Empty Window"
            }

        curr_counts, _ = np.histogram(curr_data, bins=self.num_buckets, range=self.bucket_range)
        # Apply Laplace / Lidstone smoothing
        smoothed_curr = curr_counts.astype(np.float32) + self.smoothing_factor
        curr_probs = smoothed_curr / np.sum(smoothed_curr)

        # PSI = sum( (P_curr - P_ref) * ln(P_curr / P_ref) )
        psi_elements = (curr_probs - self.ref_probs) * np.log(curr_probs / self.ref_probs)
        psi = float(np.sum(psi_elements))

        # KL = sum( P_curr * ln(P_curr / P_ref) )
        kl_div = float(np.sum(curr_probs * np.log(curr_probs / self.ref_probs)))

        # Guard against minor floating point precision negatives
        psi = max(0.0, psi)
        kl_div = max(0.0, kl_div)

        status_code = self._get_status_code(psi)
        status_message = self._get_status_message(status_code)

        return {
            **base_metrics,
            "psi": round(psi, 6),
            "kl_div": round(kl_div, 6),
            "status_code": status_code,
            "status_message": status_message
        }

    @staticmethod
    def _get_status_code(psi: float) -> int:
        if psi < 0.10:
            return 0  # Stable
        elif psi < 0.25:
            return 1  # Moderate Drift
        else:
            return 2  # Critical Drift

    @staticmethod
    def _get_status_message(status_code: int) -> str:
        if status_code == 0:
            return "Stable"
        elif status_code == 1:
            return "Moderate Drift"
        else:
            return "Critical Drift"

    def reset(self):
        """Clears all sliding window samples and resets baseline calibration."""
        self.window.clear()
        self.total_samples = 0
        self.ref_probs = None
        self.bucket_range = None
        self.is_ready = False
