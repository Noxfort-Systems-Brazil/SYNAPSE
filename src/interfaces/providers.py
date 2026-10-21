# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Any, List, Protocol, runtime_checkable


@runtime_checkable
class ITopologyProvider(Protocol):
    """Interface for components that only need to READ map/graph topology data."""
    def get_all_nodes(self) -> List[Any]: ...
    def get_all_edges(self) -> List[Any]: ...


@runtime_checkable
class ISourceProvider(Protocol):
    """Interface for components that only need to READ sensor data sources."""
    def get_all_data_sources(self) -> List[Any]: ...
    def get_data_source(self, source_id: str) -> Any: ...


@runtime_checkable
class ISensorCalibrator(Protocol):
    """Contract for dynamic sensor calibration and online bias correction."""
    def update_observability(self, active_mask: Any) -> None: ...
    def apply(self, raw_output: Any, current_history: Any, observability_mask: Any = None) -> Any: ...
    def reset(self) -> None: ...
