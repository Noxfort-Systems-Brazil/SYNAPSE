# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Any, Optional, Protocol, runtime_checkable
from src.interfaces.base import IDeviceMovable


@runtime_checkable
class IAgent(IDeviceMovable, Protocol):
    """Base contract for any AI Agent in the system."""
    ...


@runtime_checkable
class ISpatialAgent(IAgent, Protocol):
    """Contract for agents that understand space (e.g. GATv2)."""
    def process_region(self, node_features: Any, edge_index: Any) -> Any:
        """Processes a graph snapshot and returns node embeddings."""
        ...


@runtime_checkable
class ITemporalAgent(IAgent, Protocol):
    """Contract for agents that understand time (e.g. Transformers / TCN)."""
    def predict_state(self, history: Any) -> Any:
        """Predicts future states based on historical time-series."""
        ...


@runtime_checkable
class IAgentFactory(Protocol):
    """Contract for agent lifecycle and ephemeral quarantine agent management."""
    def get_or_create_linguist(self, source_id: str) -> Any: ...
    def release_linguist(self, source_id: str) -> None: ...
    def get_or_create_compass(self, source_id: str) -> Any: ...
    def release_compass(self, source_id: str) -> None: ...
    def get_or_create_cartographer(self, source_id: str, app_state: Optional[Any] = None) -> Optional[Any]: ...
    def release_cartographer(self, source_id: str) -> None: ...
    def get_or_create_specialist(self, source_id: str) -> Any: ...
    def get_or_create_auditor(self, source_id: str) -> Any: ...
    def get_or_create_jurist(self, source_id: str) -> Any: ...

