# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import torch
import torch.nn as nn
from abc import ABC, abstractmethod
from typing import Any

# Import Interface for type checking compliance
from src.interfaces.agents import IAgent
from src.utils.logging_setup import get_logger

logger = get_logger("BaseAgent")

# FIX V3: BaseAgent now inherits from nn.Module.
# This unifies the interface for 'to()', 'cuda()', 'cpu()', 'state_dict()'
# and resolves MRO (Method Resolution Order) and device placement conflicts.
class BaseAgent(nn.Module, ABC, IAgent):
    """
    Abstract Base Class for Neural Inference Agents in SYNAPSE.
    
    SOLID Architecture (Segregated Interfaces & Liskov Compliance):
    - [SRP] Manages device movement (CPU/GPU) and forward inference contract.
    - [LSP] Inference-only agents (e.g. LLM Jurist) do not require artificial training stubs.
    - [ISP] Base interface enforces only inference; training contract is extended by BaseTrainableAgent.
    - [DIP] Supports both Inheritance (self is model) and Composition (self has model).
    """

    def __init__(self, model: nn.Module = None, name: str = "UnknownAgent"):
        # Initialize nn.Module first (crucial for parameter registration)
        super().__init__()
        
        self.name = name
        self.device = torch.device("cpu")
        
        # Model Management (Inheritance vs Composition)
        # If an external model is passed and is not self, store it.
        if model is not None and model is not self:
            self._external_model = model
            # Register as submodule so that .to() propagates automatically
            if isinstance(model, nn.Module):
                self.add_module("_external_model_ref", model)
        else:
            self._external_model = None

    @property
    def model(self) -> nn.Module:
        """
        Returns the active model.
        """
        if self._external_model:
            return self._external_model
        return self

    def to(self, *args, **kwargs):
        """
        Overrides native PyTorch .to() to ensure 'self.device'
        is cascaded properly across both inheritance and composition.
        """
        # Extract device from args/kwargs if present
        device = None
        for arg in args:
            if isinstance(arg, (torch.device, str)):
                device = torch.device(arg)
                break
        if "device" in kwargs:
            device = torch.device(kwargs["device"])
            
        if device is not None:
            self.device = device
        
        # 1. Move base structure (base nn.Module)
        super().to(*args, **kwargs)
        
        # 2. If composition is used (external model), move it as well
        if self._external_model:
            self._external_model.to(*args, **kwargs)
            
        return self

    def load_weights(self, path: str):
        """Standard interface for loading model state."""
        try:
            # Load into configured device
            checkpoint = torch.load(path, map_location=self.device)
            self.model.load_state_dict(checkpoint)
        except Exception as e:
            logger.warning(f"[{self.name}] Failed to load weights from '{path}': {e}")

    def save_weights(self, path: str):
        """Standard interface for saving model state."""
        try:
            torch.save(self.model.state_dict(), path)
        except Exception as e:
            logger.error(f"[{self.name}] Failed to save weights: {e}")

    @abstractmethod
    def inference(self, input_data: Any) -> Any:
        """Primary inference method."""
        pass
    
    def train_step(self, batch_data: Any) -> float:
        """
        Optional training step returning loss.
        Default implementation for inference-only agents returns 0.0 (LSP-safe).
        """
        return 0.0


class BaseTrainableAgent(BaseAgent):
    """
    Contract for Neural Agents that execute self-contained local optimization steps.
    """
    @abstractmethod
    def train_step(self, batch_data: Any) -> float:
        """Single training step returning loss."""
        pass
