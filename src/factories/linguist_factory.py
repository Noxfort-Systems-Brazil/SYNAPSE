# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Dict, Any, Optional

from src.agents.linguist_agent import LinguistAgent
from src.pipeline.linguist_pipeline import LinguistPipeline
from src.trainer.linguist_trainer import LinguistTrainer
from src.utils.model_paths import get_modernbert_path


class LinguistFactory:
    """
    Dedicated Creational Factory for the Linguist Subsystem.
    
    SOLID Compliance (SRP / DIP):
    - Sole Responsibility: Assembles LinguistPipeline, LinguistTrainer, and injects them into LinguistAgent.
    """

    @staticmethod
    def create(
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> LinguistAgent:
        cfg = (config or {}).get('linguist', {})

        model_name = kwargs.get('model_name', cfg.get('model_name', get_modernbert_path()))
        learning_rate = kwargs.get('learning_rate', cfg.get('lr', 1e-4))
        latent_dim = kwargs.get('latent_dim', cfg.get('latent_dim', 64))
        kernel_size = kwargs.get('kernel_size', cfg.get('kernel_size', 3))

        pipeline = LinguistPipeline(
            model_name=model_name,
            latent_dim=latent_dim,
            kernel_size=kernel_size
        )
        trainer = LinguistTrainer(
            model=pipeline.model,
            tokenizer=pipeline.tokenizer,
            model_name=model_name,
            learning_rate=learning_rate,
            device=pipeline.device
        )

        return LinguistAgent(
            pipeline=pipeline,
            trainer=trainer,
            model_name=model_name,
            latent_dim=latent_dim,
            kernel_size=kernel_size,
            learning_rate=learning_rate
        )
