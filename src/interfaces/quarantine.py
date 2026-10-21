# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Any, List, Tuple, Protocol, runtime_checkable
import numpy as np


@runtime_checkable
class ISeriesExtractorPipeline(Protocol):
    """Contract for extracting and sanitizing 1D numeric time-series from raw sensor payloads."""
    def extract(self, data_chunk: List[Any]) -> np.ndarray:
        """Parses a chunk of raw heterogeneous data items into a 1D float32 NumPy array."""
        ...


@runtime_checkable
class ISemanticClassifier(Protocol):
    """Contract for inferring traffic semantic types, engineering units, and confidence scores."""
    def classify(self, source: Any, data_np: np.ndarray, data_chunk: List[Any]) -> Tuple[str, str, float]:
        """Returns a tuple containing (semantic_type, unit, confidence_score)."""
        ...


@runtime_checkable
class ISensorPhysicsValidator(Protocol):
    """Contract for verifying symbolic traffic invariants and Neuro-PINN physical consistency."""
    def validate(self, source: Any, data_np: np.ndarray, data_chunk: List[Any], agent: Any) -> bool:
        """Returns True if the sensor data complies with all physical laws and PINN thresholds."""
        ...


@runtime_checkable
class IKnowledgeTransfer(Protocol):
    """Contract for transferring neural representations (encoders/weights) between agents."""
    def transfer(self, source_agent: Any, target_agent: Any) -> bool:
        """Transfers learned feature representation from source agent to target agent."""
        ...


__all__ = [
    "ISeriesExtractorPipeline",
    "ISemanticClassifier",
    "ISensorPhysicsValidator",
    "IKnowledgeTransfer"
]
