# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Dict, Any, Optional

from src.agents.jurist_agent import JuristAgent
from src.utils.model_paths import get_qwen_gguf_path


class JuristFactory:
    """
    Dedicated Creational Factory for the Jurist Subsystem.
    
    SOLID Compliance (SRP):
    - Sole Responsibility: Instantiates JuristAgent configured with the target LLM Model Vault identifier.
    """

    @staticmethod
    def create(
        config: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> JuristAgent:
        cfg = (config or {}).get('jurist', {})
        model_id = kwargs.get('model_id', cfg.get('model_id', get_qwen_gguf_path()))
        return JuristAgent(model_id=model_id)
