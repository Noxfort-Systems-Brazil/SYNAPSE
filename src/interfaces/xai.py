# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Any, Callable, Dict, List, Optional, Protocol, Tuple, runtime_checkable
import torch


@runtime_checkable
class IXAIStrategy(Protocol):
    """
    Contract for model-specific XAI strategies.
    Encapsulates shadow model creation, forward/loss wrappers, and fallback semantic texts.
    """

    def prepare_wrapper(
        self,
        input_vector: List[float],
        model_config: Dict[str, Any],
        device: torch.device
    ) -> Callable[[torch.Tensor], torch.Tensor]:
        """Prepares and returns a callable PyTorch model wrapper suitable for gradient attribution."""
        ...

    def generate_fallback_text(
        self,
        delta: float,
        sig_map: Dict[str, float],
        attr_list: List[float]
    ) -> str:
        """Generates fallback contextual explanation text when LLM Jurist is not available."""
        ...


@runtime_checkable
class IXAIStrategyRegistry(Protocol):
    """Contract for registry mapping target model keys to IXAIStrategy instances."""

    def register(self, target: str, strategy: IXAIStrategy) -> None:
        """Registers a new XAI strategy for a specific target model."""
        ...

    def get(self, target: str) -> Optional[IXAIStrategy]:
        """Retrieves the strategy associated with the target model key."""
        ...


@runtime_checkable
class IXAIExplainer(Protocol):
    """Contract for mathematical attribution engines (e.g. Integrated Gradients)."""

    def compute_attributions(
        self,
        model_wrapper: Callable[[torch.Tensor], torch.Tensor],
        input_vector: List[float],
        device: torch.device
    ) -> Tuple[List[float], float]:
        """
        Computes feature attributions and convergence delta for an input vector.
        Returns: (attribution_list, convergence_delta).
        """
        ...


@runtime_checkable
class IXAIReporter(Protocol):
    """Contract for semantic interpretation report generation and resource management."""

    def generate_report(
        self,
        target: str,
        attr_list: List[float],
        feature_names: List[str],
        timestamp: str,
        delta: float,
        strategy: Optional[IXAIStrategy] = None
    ) -> str:
        """Generates a semantic report (via Jurist LLM or fallback strategy)."""
        ...

    def unload_resources(self) -> None:
        """Releases heavy resources (such as LLM weights in VRAM)."""
        ...
