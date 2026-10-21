# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Dict, Any, Optional

from src.agents.coordinator_agent import CoordinatorAgent
from src.pipeline.coordinator_pipeline import CoordinatorPipeline
from src.trainer.coordinator_trainer import CoordinatorTrainer


class CoordinatorFactory:
    """
    Dedicated Creational Factory for the Coordinator Subsystem.
    
    SOLID Compliance (SRP / DIP):
    - Sole Responsibility: Assembles CoordinatorPipeline, CoordinatorTrainer, and injects them into CoordinatorAgent.
    """

    @staticmethod
    def create(
        config: Optional[Dict[str, Any]] = None,
        input_dim: int = 32,
        hidden_dim: int = 32,
        output_dim: int = 32,
        **kwargs: Any
    ) -> CoordinatorAgent:
        cfg = (config or {}).get('coordinator', {})

        heads = kwargs.get('heads', cfg.get('heads', 4))
        dropout = kwargs.get('dropout', cfg.get('dropout', 0.6))
        learning_rate = kwargs.get('learning_rate', cfg.get('lr', 0.005))
        hidden_channels = kwargs.get('hidden_channels', cfg.get('hidden_channels', hidden_dim))

        pipeline = CoordinatorPipeline(
            in_channels=input_dim,
            hidden_channels=hidden_channels,
            out_channels=output_dim,
            heads=heads,
            dropout=dropout
        )

        trainer = CoordinatorTrainer(
            model=pipeline.model,
            learning_rate=learning_rate,
            device=pipeline.device
        )

        return CoordinatorAgent(
            pipeline=pipeline,
            trainer=trainer,
            in_channels=input_dim,
            hidden_channels=hidden_channels,
            out_channels=output_dim,
            heads=heads,
            dropout=dropout,
            learning_rate=learning_rate
        )
