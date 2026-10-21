# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import logging
from typing import Dict, Optional
import torch
import torch.nn as nn
from safetensors.torch import save_file, load_file


class SafetensorsRepository:
    """
    Dedicated infrastructure repository for serializing and deserializing PyTorch tensors
    and model weights using the high-performance SafeTensors format.
    Isolates file system I/O from domain neural network classes (SRP/DIP).
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    def save_tensors(self, tensors: Dict[str, torch.Tensor], filepath: str) -> bool:
        """
        Saves a dictionary of tensors to a safetensors file.
        Ensures tensors are contiguous and on CPU before saving.
        """
        if not tensors:
            self.logger.warning("Tensor dictionary is empty. Skipping safetensors export.")
            return False

        try:
            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
            # Safetensors requires contiguous memory tensors on CPU
            tensors_to_save = {k: v.contiguous().cpu() for k, v in tensors.items()}
            save_file(tensors_to_save, filepath)
            self.logger.info(f"Successfully serialized {len(tensors_to_save)} tensors to {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save tensors to safetensors at {filepath}: {e}")
            return False

    def load_tensors(self, filepath: str, device: str = "cpu") -> Dict[str, torch.Tensor]:
        """
        Loads a dictionary of tensors from a safetensors file.
        """
        if not os.path.exists(filepath):
            self.logger.error(f"Safetensors file not found at {filepath}")
            return {}

        try:
            tensors = load_file(filepath, device=device)
            self.logger.info(f"Successfully loaded {len(tensors)} tensors from {filepath}")
            return tensors
        except Exception as e:
            self.logger.error(f"Failed to load tensors from {filepath}: {e}")
            return {}

    def save_model_weights(self, model: nn.Module, filepath: str) -> bool:
        """
        Extracts model state_dict and serializes it to safetensors.
        """
        state = {k: v.contiguous().cpu() for k, v in model.state_dict().items()}
        return self.save_tensors(state, filepath)

    def load_model_weights(self, model: nn.Module, filepath: str, device: str = "cpu") -> bool:
        """
        Loads state_dict from safetensors and populates the model.
        """
        state = self.load_tensors(filepath, device=device)
        if not state:
            return False
        try:
            model.load_state_dict(state)
            self.logger.info(f"Successfully loaded weights into {model.__class__.__name__}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load weights into model: {e}")
            return False
