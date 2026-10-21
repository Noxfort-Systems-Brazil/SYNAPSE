# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Dict, Any, Optional

from src.agents.auditor_agent import AuditorAgent
from src.pipeline.auditor_pipeline import AuditorPipeline
from src.trainer.auditor_trainer import AuditorTrainer


class AuditorFactory:
    """
    Dedicated Creational Factory for the Auditor Subsystem.
    
    SOLID Compliance (SRP / DIP):
    - Sole Responsibility: Assembles AuditorPipeline, AuditorTrainer, and injects them into AuditorAgent.
    """

    @staticmethod
    def create(
        config: Optional[Dict[str, Any]] = None,
        input_len: int = 60,
        **kwargs: Any
    ) -> AuditorAgent:
        cfg = (config or {}).get('auditor', {})
        
        j_scale = kwargs.get('J', cfg.get('J', 2))
        q_factor = kwargs.get('Q', cfg.get('Q', 1))
        latent_dim = kwargs.get('latent_dim', cfg.get('latent_dim', 16))
        physics_weight = kwargs.get('physics_weight', cfg.get('physics_weight', 0.5))
        max_accel = kwargs.get('max_acceleration', cfg.get('max_acceleration', 10.0))
        enable_pinn = kwargs.get('enable_pinn', cfg.get('enable_pinn', True))
        lr = kwargs.get('learning_rate', cfg.get('lr', 1e-3))

        pipeline = AuditorPipeline(
            input_len=input_len,
            J=j_scale,
            Q=q_factor,
            latent_dim=latent_dim,
            physics_weight=physics_weight,
            max_acceleration=max_accel,
            enable_pinn=enable_pinn
        )

        trainer = AuditorTrainer(
            model=pipeline.model,
            learning_rate=lr,
            physics_weight=physics_weight,
            enable_pinn=enable_pinn,
            device=pipeline.device
        )

        return AuditorAgent(
            pipeline=pipeline,
            trainer=trainer,
            input_len=input_len,
            J=j_scale,
            Q=q_factor,
            latent_dim=latent_dim,
            learning_rate=lr
        )
