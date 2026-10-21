# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import torch
import numpy as np
import logging
from typing import Dict, Any, List, Optional
from transformers import AutoTokenizer
from torch.amp import autocast

from src.models.neuro_symbolic import NeuroSymbolicModel
from src.utils.model_paths import get_modernbert_path

logger = logging.getLogger("Synapse.LinguistPipeline")


class LinguistPipeline:
    """
    Dedicated Neural Pipeline for Semantic-Physical Validation and Contradiction Detection.
    Combines Transformer text embeddings, TCN autoencoding, and Modality-Conditioned PINN physical checks.
    """

    def __init__(
        self,
        model: Optional[NeuroSymbolicModel] = None,
        model_name: Optional[str] = None,
        latent_dim: int = 64,
        kernel_size: int = 3,
        anomaly_threshold: float = 0.85,
        device: Optional[torch.device] = None,
        **kwargs: Any
    ):
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        resolved_name = model_name or get_modernbert_path()
        self.model_name = resolved_name
        self.model = model or NeuroSymbolicModel(
            model_name=resolved_name,
            latent_dim=latent_dim,
            kernel_size=kernel_size
        )
        self.model.to(self.device)

        is_local = os.path.isdir(resolved_name)
        self.tokenizer = AutoTokenizer.from_pretrained(resolved_name, local_files_only=is_local)
        self.anomaly_threshold = anomaly_threshold

    def to(self, device: Any) -> 'LinguistPipeline':
        self.device = torch.device(device) if isinstance(device, str) else device
        self.model.to(self.device)
        return self

    def validate(self, input_data: Any, semantic_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Runs the semantic-physical anomaly detection loop using TCN-PINN.
        
        Args:
            input_data: Dict with 'text' and optional 'semantic_type', or raw series/text.
            semantic_type: Modality identified by the Linguist ("Vehicle Count", "Vehicle Speed", etc.).
            
        Returns:
            Dict containing validation boolean, error score, and physics residuals.
        """
        self.model.eval()

        if isinstance(input_data, dict):
            text_claim = input_data.get("text", "")
            sem_type = input_data.get("semantic_type", semantic_type)
        elif isinstance(input_data, list):
            text_claim = f"Sensor traffic stream: {input_data[:10]}"
            sem_type = semantic_type
        else:
            text_claim = str(input_data)
            sem_type = semantic_type

        inputs = self.tokenizer(
            text_claim,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=128
        )

        input_ids = inputs["input_ids"].to(self.device)
        attention_mask = inputs["attention_mask"].to(self.device)
        device_type = self.device.type if self.device.type != 'mps' else 'cpu'

        with torch.no_grad():
            with autocast(device_type=device_type, enabled=(self.device.type == 'cuda')):
                reconstruction, original, physics_residuals = self.model(
                    input_ids,
                    attention_mask,
                    semantic_type=sem_type
                )

            error = torch.nn.functional.mse_loss(reconstruction.float(), original.float(), reduction='none')
            mean_error = error.mean().item()
            physics_error = physics_residuals.get("total_physics_loss", torch.tensor(0.0)).item()

        is_valid = bool(mean_error < self.anomaly_threshold and physics_error < 0.5)

        return {
            "is_valid": is_valid,
            "is_anomaly": not is_valid,
            "error_score": mean_error,
            "physics_residual": physics_error,
            "semantic_vector": original.cpu().float().numpy()
        }
