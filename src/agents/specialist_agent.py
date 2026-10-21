# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import torch
import torch.nn as nn
import numpy as np
from typing import List, Any, Optional

from src.agents.base_agent import BaseAgent
from src.interfaces.pipelines import ISpecialistPipeline
from src.interfaces.trainers import ISpecialistTrainer
from src.pipeline.specialist_pipeline import SpecialistPipeline
from src.trainer.specialist_trainer import SpecialistTrainer


class SpecialistAgent(BaseAgent):
    """
    The Specialist Agent ('O Tático').
    
    Pure Orchestrator Architecture (SOLID Compliant):
    - Single Responsibility: Manages temporal feature extraction and local TCN model inference.
    - Delegations:
      -> TCN Execution & Embeddings: ISpecialistPipeline (src/pipeline/specialist_pipeline.py)
      -> TCN Training Routines: ISpecialistTrainer (src/trainer/specialist_trainer.py)
    """

    def __init__(
        self,
        pipeline: Optional[ISpecialistPipeline] = None,
        trainer: Optional[ISpecialistTrainer] = None,
        input_dim: int = 1,
        output_dim: int = 32,
        num_channels: Optional[List[int]] = None,
        kernel_size: int = 2,
        dropout: float = 0.2,
        learning_rate: float = 0.001,
        name: str = "SpecialistAgent",
        **kwargs: Any
    ):
        num_channels = num_channels or [16, 32]

        if pipeline is None:
            pipeline = SpecialistPipeline(
                input_dim=input_dim,
                output_dim=output_dim,
                num_channels=num_channels,
                kernel_size=kernel_size,
                dropout=dropout
            )

        model = getattr(pipeline, "model", None)
        super().__init__(model=model, name=name)

        self.pipeline: ISpecialistPipeline = pipeline
        self.trainer: ISpecialistTrainer = trainer or SpecialistTrainer(
            model=self.model,
            input_dim=input_dim,
            output_dim=output_dim,
            learning_rate=learning_rate,
            device=getattr(self.pipeline, "device", None)
        )

        self.input_dim = input_dim
        self.output_dim = output_dim
        self.num_channels = num_channels
        self.kernel_size = kernel_size
        self.dropout = dropout
        self.learning_rate = learning_rate

        # Shortcuts for compatibility
        self.tcn = self.model["tcn"]
        self.decoder = self.model["decoder"] if "decoder" in self.model else None
        self.reconstruction_head = self.model["reconstruction_head"] if "reconstruction_head" in self.model else None

        # Extractor and Modality attached by the Linguist
        self.extractor: Optional[Any] = None
        self.semantic_type: Optional[str] = None
        self.inferred_unit: Optional[str] = None

        # Directional Orientation attached by the CompassAgent
        self.orientation_vector: Optional[Any] = None
        self.target_edge_id: Optional[str] = None
        self.channel_key: Optional[str] = None

        # Training Metrics
        self.running_loss = 0.0
        self.steps = 0

    def set_extractor(
        self,
        extractor: Any,
        semantic_type: Optional[str] = None,
        unit: Optional[str] = None
    ) -> 'SpecialistAgent':
        """
        Attaches the extraction pipeline and modality taught by the Linguist,
        enabling this local TCN to process raw sensor packets autonomously.
        """
        self.extractor = extractor
        self.semantic_type = semantic_type
        self.inferred_unit = unit
        return self

    def set_orientation(
        self,
        vector: Optional[Any] = None,
        edge_id: Optional[str] = None,
        channel_key: Optional[str] = None
    ) -> 'SpecialistAgent':
        """
        Attaches the directional orientation taught by the CompassAgent,
        enabling this local TCN to align its temporal embeddings with the directed road graph.
        """
        self.orientation_vector = vector
        self.target_edge_id = edge_id
        self.channel_key = channel_key
        return self

    @property
    def optimizer(self):
        """Delegates optimizer access to the underlying trainer."""
        opt = getattr(self.trainer, "optimizer", None)
        return opt if opt is not None else getattr(self, "_optimizer", None)

    def freeze(self) -> 'SpecialistAgent':
        """Freezes specialist weights for drift-safe real-time inference (Freeze phase)."""
        freeze_fn = getattr(self.pipeline, "freeze", None)
        if callable(freeze_fn):
            freeze_fn()
        return self

    def unfreeze(self) -> 'SpecialistAgent':
        """Unfreezes specialist weights for dynamic recalibration."""
        unfreeze_fn = getattr(self.pipeline, "unfreeze", None)
        if callable(unfreeze_fn):
            unfreeze_fn()
        return self

    @property
    def is_frozen(self) -> bool:
        return bool(getattr(self.pipeline, "is_frozen", False))

    def inference(self, input_data: Any) -> Any:
        """
        Standard Interface Wrapper: accepts either raw sensor packets (using its attached extractor)
        or numerical time-series arrays, and outputs 32-dim latent space embeddings.
        """
        return self.predict(input_data)

    def predict(self, input_sequence: Any) -> np.ndarray:
        """
        Processes the input sequence or raw payload and returns TCN latent embeddings.
        """
        # If input is a raw dictionary, list of dicts, or unparsed payload, use attached extractor
        if isinstance(input_sequence, (dict, list)) and self.extractor is not None:
            if isinstance(input_sequence, dict):
                input_data = [input_sequence]
            else:
                input_data = input_sequence
            if len(input_data) > 0 and isinstance(input_data[0], (dict, str)):
                seq_np = self.extractor.extract(input_data)
                return self.pipeline.predict(seq_np)

        return self.pipeline.predict(input_sequence)

    def compute_loss(self, input_sequence: Any) -> float:
        """Evaluates reconstruction loss via fast forward-pass without backpropagation."""
        loss_fn = getattr(self.pipeline, "compute_loss", None)
        if callable(loss_fn):
            return loss_fn(input_sequence)
        return 0.02

    def train_step(self, batch_data: Any) -> float:
        """Delegates training step to SpecialistTrainer."""
        return self.trainer.train_step(batch_data)

    def train(self, inputs: torch.Tensor, targets: torch.Tensor, epochs: int = 1, batch_size: int = 32) -> float:
        """Delegates training loop to SpecialistTrainer and tracks running loss."""
        avg_loss = self.trainer.train(inputs, targets, epochs=epochs, batch_size=batch_size)
        self.running_loss = 0.9 * self.running_loss + 0.1 * avg_loss if self.steps > 0 else avg_loss
        self.steps += 1
        return avg_loss

    def _update_dropout_layers(self):
        """Updates all dropout layers in the model to the current rate."""
        if isinstance(self.model, nn.Module):
            for m in self.model.modules():
                if isinstance(m, (nn.Dropout, nn.Dropout1d, nn.Dropout2d)):
                    m.p = self.dropout
        elif isinstance(self.model, dict):
            for sub_mod in self.model.values():
                if isinstance(sub_mod, nn.Module):
                    for m in sub_mod.modules():
                        if isinstance(m, (nn.Dropout, nn.Dropout1d, nn.Dropout2d)):
                            m.p = self.dropout

    # --- Persistence Primitives ---

    def get_state(self) -> dict:
        """Returns the agent's internal neural state dictionary."""
        state = {
            "agent_weights": {
                "tcn": self.tcn.state_dict(),
            },
            "agent_config": {
                "lr": self.learning_rate,
                "dropout": self.dropout,
            }
        }
        if isinstance(self.decoder, nn.Module):
            state["agent_weights"]["decoder"] = self.decoder.state_dict()
        if isinstance(self.reconstruction_head, nn.Module):
            state["agent_weights"]["head"] = self.reconstruction_head.state_dict()
        return state

    def set_state(self, state: dict):
        """Loads weights and configuration safely into components."""
        weights = state.get("agent_weights", {})
        if "tcn" in weights:
            self.tcn.load_state_dict(weights["tcn"])
        if isinstance(self.decoder, nn.Module) and "decoder" in weights:
            self.decoder.load_state_dict(weights["decoder"])
        if isinstance(self.reconstruction_head, nn.Module) and "head" in weights:
            self.reconstruction_head.load_state_dict(weights["head"])

        conf = state.get("agent_config", {})
        if "lr" in conf:
            self.learning_rate = conf["lr"]
            opt = self.optimizer
            if opt is not None:
                for param_group in opt.param_groups:
                    param_group['lr'] = self.learning_rate
        if "dropout" in conf:
            self.dropout = conf["dropout"]
            self._update_dropout_layers()

