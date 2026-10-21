# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Dict, Any, Optional

from src.agents.imputer_agent import ImputerAgent
from src.pipeline.imputer_pipeline import ImputerPipeline
from src.trainer.imputer_trainer import ImputerTrainer


class ImputerFactory:
    """
    Dedicated Creational Factory for the Imputer Subsystem.
    
    SOLID Compliance (SRP / DIP):
    - Sole Responsibility: Assembles ImputerPipeline, ImputerTrainer, and injects them into ImputerAgent.
    """

    @staticmethod
    def create(
        config: Optional[Dict[str, Any]] = None,
        feature_dim: int = 4,
        **kwargs: Any
    ) -> ImputerAgent:
        cfg = (config or {}).get('imputer', {})

        seq_len = kwargs.get('seq_len', cfg.get('seq_len', 24))
        patch_len = kwargs.get('patch_len', cfg.get('patch_len', 8))
        stride = kwargs.get('stride', cfg.get('stride', 4))
        d_model = kwargs.get('d_model', cfg.get('d_model', 64))
        n_heads = kwargs.get('n_heads', cfg.get('n_heads', 4))
        n_layers = kwargs.get('n_layers', cfg.get('n_layers', 2))
        dropout = kwargs.get('dropout', cfg.get('dropout', 0.1))
        learning_rate = kwargs.get('learning_rate', cfg.get('lr', 0.001))

        pipeline = ImputerPipeline(
            feature_dim=feature_dim,
            seq_len=seq_len,
            patch_len=patch_len,
            stride=stride,
            d_model=d_model,
            n_heads=n_heads,
            n_layers=n_layers,
            dropout=dropout
        )

        trainer = ImputerTrainer(
            model=pipeline.model,
            learning_rate=learning_rate,
            device=pipeline.device
        )

        return ImputerAgent(
            pipeline=pipeline,
            trainer=trainer,
            feature_dim=feature_dim,
            seq_len=seq_len,
            patch_len=patch_len,
            stride=stride,
            d_model=d_model,
            n_heads=n_heads,
            n_layers=n_layers,
            dropout=dropout,
            learning_rate=learning_rate
        )
