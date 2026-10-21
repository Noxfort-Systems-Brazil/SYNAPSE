# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import time
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class NodeState:
    """
    Encapsulates all mutable runtime state and metadata of a Traffic Node.
    Follows Single Responsibility Principle (SRP) by decoupling state tracking from execution pipelines.
    """
    source_id: str
    last_value: float = 0.0
    last_loss: float = 0.008
    last_psi: float = 0.012
    last_timestamp: float = field(default_factory=time.time)
    last_embedding: np.ndarray = field(default_factory=lambda: np.zeros(32))
    steps_processed: int = 0
    fallback_steps: int = 0
    updated_this_cycle: bool = False
    is_validated: bool = False
    is_rejected: bool = False

    def mark_updated(self) -> None:
        """Flags that this node received or processed a sensor reading in the current cycle."""
        self.updated_this_cycle = True

    def reset_cycle(self) -> None:
        """Resets the cycle update flag at the end of a cycle tick."""
        self.updated_this_cycle = False

    def increment_fallback(self) -> None:
        """Increments the count of consecutive synthetic fallback steps."""
        self.fallback_steps += 1

    def reset_fallback(self) -> None:
        """Resets the synthetic fallback step counter upon sensor recovery."""
        self.fallback_steps = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serializes internal state for checkpointing and telemetry."""
        return {
            "source_id": self.source_id,
            "last_value": self.last_value,
            "last_timestamp": self.last_timestamp,
            "steps_processed": self.steps_processed,
            "fallback_steps": self.fallback_steps,
            "is_validated": self.is_validated,
            "is_rejected": self.is_rejected
        }

    def from_dict(self, state_dict: Dict[str, Any]) -> None:
        """Restores state attributes from a dictionary checkpoint."""
        if not isinstance(state_dict, dict):
            return
        self.steps_processed = state_dict.get("steps_processed", self.steps_processed)
        self.fallback_steps = state_dict.get("fallback_steps", self.fallback_steps)
        self.is_validated = state_dict.get("is_validated", self.is_validated)
        self.is_rejected = state_dict.get("is_rejected", self.is_rejected)
        self.last_value = state_dict.get("last_value", self.last_value)
        self.last_timestamp = state_dict.get("last_timestamp", self.last_timestamp)
