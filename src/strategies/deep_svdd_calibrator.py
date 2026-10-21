# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import torch
from typing import Tuple, Optional, Dict, Any


from src.strategies.hybrid_dynamic_calibrator import HybridDynamicCalibrator


class DeepSVDDCalibrator:
    """
    Statistical Deep SVDD (Support Vector Data Description) Calibrator.
    
    Decoupled strategy for:
    1. Hypersphere Center Initialization (c = mean of initial baseline representations).
    2. Adaptive Tri-Modal Anomaly Threshold Tracking (Robust Median/MAD + EVT/POT + EMA).
    3. Anomaly Score Computation: ||z - c||^2.
    """

    def __init__(self, latent_dim: int, initial_threshold: float = 0.85, momentum: float = 0.1):
        self.latent_dim = latent_dim
        self.momentum = momentum
        self.center: Optional[torch.Tensor] = None
        self.center_initialized: bool = False
        
        # Tri-Modal Adaptive Ensemble (Zero Hardcoded Thresholds)
        self.dynamic_calibrator = HybridDynamicCalibrator(
            warmup_cycles=25,
            initial_fallback_floor=initial_threshold,
            ema_momentum=momentum,
        )

    @property
    def threshold(self) -> float:
        return self.dynamic_calibrator.threshold

    @threshold.setter
    def threshold(self, val: float) -> None:
        self.dynamic_calibrator.threshold = float(val)

    @property
    def current_threshold(self) -> float:
        return self.dynamic_calibrator.threshold

    def load_calibrated_state(self, threshold: float) -> None:
        """Marks dynamic calibrator as pre-warmed using offline calibrated threshold."""
        self.dynamic_calibrator.load_calibrated_state(threshold)

    def init_center(self, z: torch.Tensor) -> torch.Tensor:
        """
        Initializes the hypersphere center 'c' as the mean of baseline latent vectors.
        """
        with torch.no_grad():
            self.center = torch.mean(z.float(), dim=0, keepdim=True).detach()
            self.center_initialized = True
            return self.center

    def update_threshold(self, anomaly_scores: torch.Tensor) -> float:
        """
        Updates the anomaly threshold based on the statistics of current batch (mean + 2*std)
        and updates the dynamic ensemble calibrator.
        """
        with torch.no_grad():
            std_val = anomaly_scores.std().item() if anomaly_scores.numel() > 1 else 0.0
            mean_val = anomaly_scores.mean().item()
            current_limit = mean_val + 2.0 * std_val
            # Feed mean into dynamic calibrator
            self.dynamic_calibrator.evaluate(mean_val)
            return self.threshold

    def evaluate(self, score: float) -> Tuple[bool, float, Dict[str, Any]]:
        """Evaluates an anomaly score against the dynamic tri-modal ensemble."""
        return self.dynamic_calibrator.evaluate(score)

    def compute_anomaly_scores(self, z: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Computes Deep SVDD anomaly score: ||z - center||^2 and binary classification mask.
        
        Args:
            z: Latent representations [Batch, LatentDim]
        Returns:
            scores: Euclidean distances to center [Batch]
            is_anomaly: Boolean tensor indicating if score exceeds adaptive threshold [Batch]
        """
        if not self.center_initialized or self.center is None:
            self.init_center(z)
            
        center = self.center.to(z.device)
        scores = torch.sum((z - center) ** 2, dim=-1)
        is_anomaly = scores > self.threshold
        return scores, is_anomaly
