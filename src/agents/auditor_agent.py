# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import torch
from typing import Dict, Any, Union, Optional

from src.agents.base_agent import BaseAgent
from src.interfaces.pipelines import IAuditorPipeline
from src.interfaces.trainers import IAuditorTrainer
from src.pipeline.auditor_pipeline import AuditorPipeline
from src.trainer.auditor_trainer import AuditorTrainer


class AuditorAgent(BaseAgent):
    """
    The Auditor Agent ('O Segurança').
    
    Pure Orchestrator Architecture (SOLID Compliant):
    - Single Responsibility: High-level security auditing and anomaly detection.
    - Delegations:
      -> Neural Pipeline & Scoring: IAuditorPipeline (src/pipeline/auditor_pipeline.py)
      -> Neural Optimization & Calibration: IAuditorTrainer (src/trainer/auditor_trainer.py)
    """

    def __init__(
        self,
        pipeline: Optional[IAuditorPipeline] = None,
        trainer: Optional[IAuditorTrainer] = None,
        input_len: int = 60,
        J: int = 2,
        Q: int = 1,
        latent_dim: int = 16,
        learning_rate: float = 1e-3,
        physics_weight: float = 0.5,
        max_acceleration: float = 10.0,
        enable_pinn: bool = True,
        name: str = "AuditorAgent",
        **kwargs: Any
    ):
        if pipeline is None:
            pipeline = AuditorPipeline(
                input_len=input_len,
                J=J,
                Q=Q,
                latent_dim=latent_dim,
                physics_weight=physics_weight,
                max_acceleration=max_acceleration,
                enable_pinn=enable_pinn
            )

        model = getattr(pipeline, "model", None)
        super().__init__(model=model, name=name)

        self.pipeline: IAuditorPipeline = pipeline
        self.trainer: IAuditorTrainer = trainer or AuditorTrainer(
            model=self.model,
            calibrator=getattr(self.pipeline, "calibrator", None),
            learning_rate=learning_rate,
            physics_weight=physics_weight,
            enable_pinn=enable_pinn,
            device=getattr(self.pipeline, "device", None)
        )

    def inference(self, input_data: Union[Dict[str, Any], torch.Tensor]) -> Dict[str, Any]:
        """Unified inference entry point."""
        return self.audit(input_data)

    def audit(self, input_data: Union[Dict[str, Any], torch.Tensor]) -> Dict[str, Any]:
        """Delegates security and physics auditing to AuditorPipeline."""
        return self.pipeline.audit(input_data)

    def reset_history(self):
        """Delegates anomaly history reset to AuditorPipeline."""
        reset_fn = getattr(self.pipeline, "reset_history", None)
        if callable(reset_fn):
            reset_fn()

    def train_step(self, input_data: Any) -> float:
        """Delegates optimization and adaptive threshold updates to AuditorTrainer."""
        return self.trainer.train_step(input_data)

    def apply_calibration(
        self,
        model_state_dict: Optional[Dict[str, Any]] = None,
        threshold: Optional[Union[float, torch.Tensor]] = None,
        center: Optional[torch.Tensor] = None,
        center_initialized: Optional[bool] = None,
    ) -> None:
        """
        Applies calibrated offline parameters (weights, threshold, center)
        directly to the agent's model, pipeline, and trainer.
        Encapsulates internal calibrator topology (Law of Demeter).
        """
        if model_state_dict is not None and self.model is not None:
            self.model.load_state_dict(model_state_dict)

        if threshold is not None:
            raw_val = float(threshold.item() if isinstance(threshold, torch.Tensor) else threshold)
            thresh_val = max(0.75, raw_val * 1.35 if raw_val < 0.60 else raw_val)
            if self.model is not None:
                self.model.threshold = torch.tensor(thresh_val)

            for target in (getattr(self.pipeline, "calibrator", None), getattr(self.trainer, "calibrator", None)):
                if target is not None:
                    load_cal_fn = getattr(target, "load_calibrated_state", None)
                    if callable(load_cal_fn):
                        load_cal_fn(thresh_val)
                    else:
                        target.threshold = thresh_val

        if center is not None:
            c = center.float() if isinstance(center, torch.Tensor) else center
            c_init = True if center_initialized is None else center_initialized
            if self.model is not None:
                self.model.center = c
                self.model.center_initialized = c_init

            for target in (getattr(self.pipeline, "calibrator", None), getattr(self.trainer, "calibrator", None)):
                if target is not None:
                    target.center = c
                    target.center_initialized = c_init

    def set_default_threshold(self, safe_floor: float = 0.85) -> None:
        """Sets the fallback baseline floor threshold."""
        if self.model is not None:
            self.model.threshold = torch.tensor(safe_floor)
        cal = getattr(self.pipeline, "calibrator", None)
        if cal is not None:
            cal.threshold = safe_floor

