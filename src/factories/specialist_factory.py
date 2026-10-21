# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Dict, Any, Optional

from src.agents.specialist_agent import SpecialistAgent
from src.pipeline.specialist_pipeline import SpecialistPipeline
from src.trainer.specialist_trainer import SpecialistTrainer


class SpecialistFactory:
    """
    Dedicated Creational Factory for the Specialist Subsystem.
    
    SOLID Compliance (SRP / DIP):
    - Sole Responsibility: Assembles SpecialistPipeline, SpecialistTrainer, and injects them into SpecialistAgent.
    """

    @staticmethod
    def create(
        config: Optional[Dict[str, Any]] = None,
        input_dim: int = 1,
        output_dim: int = 32,
        **kwargs: Any
    ) -> SpecialistAgent:
        cfg = (config or {}).get('specialist', {})

        num_channels = kwargs.get('num_channels')
        if num_channels is None:
            if 'num_levels' in cfg and 'base_channel' in cfg:
                num_channels = [cfg['base_channel']] * cfg['num_levels']
            else:
                num_channels = [16, 32]

        kernel_size = kwargs.get('kernel_size', cfg.get('kernel_size', 2))
        dropout = kwargs.get('dropout', cfg.get('dropout', 0.2))
        learning_rate = kwargs.get('learning_rate', cfg.get('lr', 0.001))

        pipeline = SpecialistPipeline(
            input_dim=input_dim,
            output_dim=output_dim,
            num_channels=num_channels,
            kernel_size=kernel_size,
            dropout=dropout
        )

        trainer = SpecialistTrainer(
            model=pipeline.model,
            input_dim=input_dim,
            output_dim=output_dim,
            learning_rate=learning_rate,
            device=pipeline._get_current_device()
        )

        return SpecialistAgent(
            pipeline=pipeline,
            trainer=trainer,
            input_dim=input_dim,
            output_dim=output_dim,
            num_channels=num_channels,
            kernel_size=kernel_size,
            dropout=dropout,
            learning_rate=learning_rate
        )
