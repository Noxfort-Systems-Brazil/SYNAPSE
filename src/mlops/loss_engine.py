# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import numpy as np
from typing import Optional, Union, Sequence


class LossEngine:
    """
    Pure numerical calculation engine for MLOps loss and physical residuals.
    
    Responsibilities:
    - Reconstruction Loss (Normalized Mean Squared Error / MAE).
    - Hydrodynamic Physical Residuals (q = k * v conservation law).
    - Zero dependency on PyTorch computational graphs / autograd.
    """

    @staticmethod
    def compute_reconstruction_loss(
        target: Optional[Union[np.ndarray, Sequence[float]]],
        prediction: Optional[Union[np.ndarray, Sequence[float]]],
        epsilon: float = 1e-6
    ) -> float:
        """
        Computes normalized Mean Squared Error (NMSE) between target and prediction.
        
        NMSE = MSE(target, prediction) / (Var(target) + epsilon)
        Normalized to ensure consistent scale regardless of physical units (km/h vs veh/h).
        """
        if target is None or prediction is None:
            return 0.0

        t = np.asarray(target, dtype=np.float32)
        p = np.asarray(prediction, dtype=np.float32)

        if t.size == 0 or p.size == 0:
            return 0.0

        if t.shape != p.shape:
            if t.size == p.size:
                t = t.flatten()
                p = p.flatten()
            elif t.ndim >= 2 and t[-1].size == p.size:
                t = t[-1].flatten()
                p = p.flatten()
            elif p.ndim >= 2 and p[0].size == t.size:
                p = p[0].flatten()
                t = t.flatten()
            else:
                return 0.0

        # Replace non-finite values if present
        valid_mask = np.isfinite(t) & np.isfinite(p)
        if not np.any(valid_mask):
            return 0.0

        t_clean = t[valid_mask]
        p_clean = p[valid_mask]

        mse = np.mean((t_clean - p_clean) ** 2)
        var_t = np.var(t_clean)

        nmse = float(mse / (var_t + epsilon)) if var_t > epsilon else float(mse)
        return max(0.0, nmse)

    @staticmethod
    def compute_hydrodynamic_residual(
        speed: Optional[Union[np.ndarray, Sequence[float]]],
        density: Optional[Union[np.ndarray, Sequence[float]]],
        flow: Optional[Union[np.ndarray, Sequence[float]]],
        speed_in_kmh: bool = True
    ) -> float:
        """
        Computes physical conservation residual: |q - (k * v)|.
        
        If speed is in km/h:
        q (veh/h) = k (veh/km) * v (km/h).
        """
        if speed is None or density is None or flow is None:
            return 0.0

        s = np.asarray(speed, dtype=np.float32)
        k = np.asarray(density, dtype=np.float32)
        q = np.asarray(flow, dtype=np.float32)

        if s.size == 0 or k.size == 0 or q.size == 0:
            return 0.0

        valid_mask = np.isfinite(s) & np.isfinite(k) & np.isfinite(q)
        if not np.any(valid_mask):
            return 0.0

        s_val = s[valid_mask]
        k_val = k[valid_mask]
        q_val = q[valid_mask]

        # Hydrodynamic fundamental equation: q_expected = k * v
        q_expected = k_val * s_val
        residual = np.abs(q_val - q_expected)
        norm_factor = np.maximum(q_val, 1.0)

        rel_error = np.mean(residual / norm_factor)
        return float(np.clip(rel_error, 0.0, 1.0))
