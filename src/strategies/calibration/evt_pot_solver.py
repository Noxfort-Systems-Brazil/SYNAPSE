# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import numpy as np


class EvtPotSolver:
    """
    Peaks-Over-Threshold (POT) using Generalized Pareto Distribution (GPD).
    Analytically models the tail of neural loss residuals above a dynamic threshold u.
    """

    @staticmethod
    def compute_evt_pot(
        arr: np.ndarray,
        median_val: float,
        sigma_mad: float,
        risk_p: float = 1e-3,
    ) -> float:
        """
        Peaks-Over-Threshold (POT) using Generalized Pareto Distribution (GPD).
        Models the tail of excesses above threshold u.
        """
        u = median_val + (1.2 * sigma_mad)
        excesses = arr[arr > u] - u
        n_total = len(arr)
        n_u = len(excesses)

        # If not enough tail excesses, fallback to high empirical quantile
        if n_u < 5:
            p99 = float(np.percentile(arr, 99)) if len(arr) >= 20 else median_val + 3.0 * sigma_mad
            return p99 * 1.15

        # Method of Moments estimator for GPD parameters (gamma = shape, sigma = scale)
        mean_excess = float(np.mean(excesses))
        var_excess = float(np.var(excesses)) if len(excesses) > 1 else 0.0

        if var_excess > 1e-7 and (mean_excess ** 2) < var_excess:
            # Standard GPD moment estimation
            gamma = 0.5 * (1.0 - (mean_excess ** 2) / var_excess)
            scale = 0.5 * mean_excess * ((mean_excess ** 2) / var_excess + 1.0)
            gamma = max(-0.5, min(0.5, gamma))  # Regularize shape parameter
        else:
            # Exponential tail fallback (gamma -> 0)
            gamma = 0.0
            scale = max(1e-4, mean_excess)

        # Extreme quantile calculation via GPD inverse CDF:
        # z_p = u + (scale / gamma) * [ ((n_total / n_u) * p)^(-gamma) - 1 ]
        ratio = (n_total / max(1, n_u)) * risk_p
        ratio = max(1e-6, min(0.99, ratio))

        if abs(gamma) > 1e-4:
            term = (ratio ** (-gamma)) - 1.0
            z_p = u + (scale / gamma) * term
        else:
            # Limit as gamma -> 0 (Exponential distribution)
            z_p = u - scale * np.log(ratio)

        return float(z_p)
