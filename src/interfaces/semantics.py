# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Any, Dict, List, Protocol, Tuple, runtime_checkable


@runtime_checkable
class ISemanticEmbedder(Protocol):
    """Contract for NLP semantic text embedding models."""
    def encode(self, texts: List[str]) -> Any: ...


@runtime_checkable
class ISemanticClusterer(Protocol):
    """Contract for dynamic semantic concept clustering and discovery."""
    def match_or_create_concept(
        self,
        current_embedding: Any,
        clean_texts: List[str],
        **kwargs: Any
    ) -> Tuple[str, bool]: ...

    def get_ontology_report(self) -> Dict[str, List[str]]: ...


@runtime_checkable
class IOntologyRepository(Protocol):
    """Contract for persisting ontology tensors and model checkpoints."""
    def save_tensors(self, tensors: Dict[str, Any], filepath: str) -> bool: ...
    def load_tensors(self, filepath: str, device: str = "cpu") -> Dict[str, Any]: ...
