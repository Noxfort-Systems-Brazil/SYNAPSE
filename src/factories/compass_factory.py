# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Dict, Any, Optional

from src.agents.compass_agent import CompassAgent
from src.pipeline.compass_pipeline import CompassPipeline
from src.utils.model_paths import get_modernbert_path


class CompassFactory:
    """
    Dedicated Creational Factory for the Compass Subsystem.
    
    SOLID Compliance (SRP / DIP):
    - Sole Responsibility: Assembles CompassPipeline and injects into CompassAgent.
    """

    @staticmethod
    def create(
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> CompassAgent:
        cfg = (config or {}).get('compass', {})
        model_name = kwargs.get('model_name', cfg.get('model_name', get_modernbert_path()))
        confidence_threshold = kwargs.get('confidence_threshold', cfg.get('confidence_threshold', 0.65))

        pipeline = CompassPipeline(
            model_name=model_name,
            confidence_threshold=confidence_threshold
        )

        return CompassAgent(
            pipeline=pipeline,
            model_name=model_name
        )
