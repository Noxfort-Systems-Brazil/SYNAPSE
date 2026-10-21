# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import logging
from typing import Dict, Any, List, Optional

from transformers import AutoTokenizer

from src.agents.base_agent import BaseAgent
from src.interfaces.pipelines import ILinguistPipeline
from src.interfaces.trainers import ILinguistTrainer
from src.pipeline.linguist_pipeline import LinguistPipeline
from src.trainer.linguist_trainer import LinguistTrainer
from src.utils.model_paths import get_modernbert_path

logger = logging.getLogger("Synapse.Agents.Linguist")


class LinguistAgent(BaseAgent):
    """
    The Linguist Agent ('O Validador Semântico-Físico').
    
    Pure Orchestrator Architecture (SOLID Compliant):
    - Single Responsibility: Manages semantic log validation and contradiction detection.
    - Delegations:
      -> NeuroSymbolic Reasoning & Validation: ILinguistPipeline (src/pipeline/linguist_pipeline.py)
      -> TCN-PINN Optimization: ILinguistTrainer (src/trainer/linguist_trainer.py)
    """

    def __init__(
        self,
        pipeline: Optional[ILinguistPipeline] = None,
        trainer: Optional[ILinguistTrainer] = None,
        model_name: Optional[str] = None,
        latent_dim: int = 64,
        kernel_size: int = 3,
        learning_rate: float = 1e-4,
        name: str = "LinguistAgent",
        **kwargs: Any
    ):
        resolved_name = model_name or get_modernbert_path()
        if pipeline is None:
            pipeline = LinguistPipeline(
                model_name=resolved_name,
                latent_dim=latent_dim,
                kernel_size=kernel_size
            )

        model = getattr(pipeline, "model", None)
        super().__init__(model=model, name=name)

        self.pipeline: ILinguistPipeline = pipeline
        self.trainer: ILinguistTrainer = trainer or LinguistTrainer(
            model=self.model,
            tokenizer=getattr(pipeline, "tokenizer", None),
            model_name=model_name,
            learning_rate=learning_rate,
            device=getattr(self.pipeline, "device", None)
        )

    @property
    def scaler(self):
        return getattr(self.trainer, "scaler", None)

    @property
    def anomaly_threshold(self) -> float:
        return getattr(self.pipeline, "anomaly_threshold", 0.85)

    @anomaly_threshold.setter
    def anomaly_threshold(self, value: float):
        if self.pipeline is not None:
            self.pipeline.anomaly_threshold = value

    def inference(self, input_data: Any, semantic_type: Optional[str] = None) -> Dict[str, Any]:
        """Delegates semantic-physical anomaly detection to LinguistPipeline."""
        if isinstance(input_data, dict) and "semantic_type" not in input_data and semantic_type:
            input_data["semantic_type"] = semantic_type
        validate_fn = getattr(self.pipeline, "validate", None)
        if callable(validate_fn):
            try:
                return validate_fn(input_data, semantic_type=semantic_type)
            except TypeError:
                return validate_fn(input_data)
        return self.pipeline.validate(input_data)

    def train_step(self, batch_data: Any, epochs: int = 10, semantic_type: Optional[str] = None) -> float:
        """Delegates training step to LinguistTrainer with local convergence loop."""
        train_fn = getattr(self.trainer, "train_step", None)
        if callable(train_fn):
            try:
                return train_fn(batch_data, epochs=epochs, semantic_type=semantic_type)
            except TypeError:
                return train_fn(batch_data)
        return self.trainer.train_step(batch_data)

    def calibrate_threshold(self, validation_texts: List[str]):
        """Delegates threshold auto-calibration to LinguistPipeline."""
        self.pipeline.calibrate_threshold(validation_texts)
