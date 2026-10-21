# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Dict, List, Optional, Tuple, Protocol, runtime_checkable, Any
from src.domain.entities import DataSource


@runtime_checkable
class ISourceStorage(Protocol):
    """
    Contract for storage persistence and filesystem/database I/O for data sources.
    (SRP: Pure persistence isolation).
    """

    def serialize_source(self, src: DataSource) -> dict:
        """Convert a DataSource entity to a serializable dictionary."""
        ...

    def deserialize_source(self, data: dict) -> DataSource:
        """Reconstruct a DataSource entity from dictionary data."""
        ...

    def save(
        self,
        data_sources: Dict[str, DataSource],
        associations: Dict[str, List[str]],
        map_path: Optional[str] = None
    ) -> bool:
        """Persist sources, element associations, and active map path."""
        ...

    def load(self) -> Tuple[Dict[str, DataSource], Dict[str, List[str]], Optional[str]]:
        """Load sources, element associations, and active map path from storage."""
        ...


@runtime_checkable
class ISourceProbeService(Protocol):
    """
    Contract for reachability and health checks on data sources.
    (SRP: Pure network diagnostics isolation).
    """

    def probe(self, source: DataSource) -> None:
        """Perform a non-blocking reachability test on a given data source."""
        ...


@runtime_checkable
class ISourceRepository(Protocol):
    """
    Contract for in-memory pure domain repository managing DataSources and associations.
    (SRP: Pure in-memory domain state management).
    """

    def add(self, source: DataSource) -> None:
        """Register a new DataSource in the repository."""
        ...

    def remove(self, source_id: str) -> Optional[DataSource]:
        """Remove a DataSource and clean up its associations."""
        ...

    def get(self, source_id: str) -> Optional[DataSource]:
        """Get a DataSource by ID."""
        ...

    def get_all(self) -> List[DataSource]:
        """List all registered DataSources."""
        ...

    def update_value(self, source_id: str, value: float) -> None:
        """Update the latest telemetry value of a DataSource."""
        ...

    def update_source(
        self,
        source_id: str,
        name: Optional[str] = None,
        is_local: Optional[bool] = None,
        source_type: Optional[Any] = None,
        connection_string: Optional[str] = None,
    ) -> Optional[DataSource]:
        """Update configurable properties of an existing DataSource."""
        ...

    def associate(self, source_id: str, element_id: str) -> None:
        """Associate a source with a map element (node or edge)."""
        ...

    def get_associations(self, element_id: str) -> List[str]:
        """Get source IDs associated with a given map element."""
        ...

    def get_element_for_source(self, source_id: str) -> Optional[str]:
        """Find the map element ID associated with a given source ID."""
        ...

    def get_elements_for_source(self, source_id: str) -> List[str]:
        """Find all map element IDs associated with a given source ID."""
        ...

    def toggle_origin(self, source_id: str) -> Optional[bool]:
        """Toggle a source between Local and Global scope."""
        ...

    def get_next_source_id(self) -> str:
        """Generate the next monotonic source ID in the format 'src_{n}'."""
        ...

    def clear(self) -> None:
        """Clear all registered sources and associations."""
        ...

    def set_map_path(self, map_path: Optional[str]) -> None:
        """Set the active map file path."""
        ...

    def get_map_path(self) -> Optional[str]:
        """Get the active map file path."""
        ...

    def save(self) -> None:
        """Persist current state to storage."""
        ...

    def notify_source_updated(self, source: DataSource) -> None:
        """Notify and persist updates to a data source."""
        ...

