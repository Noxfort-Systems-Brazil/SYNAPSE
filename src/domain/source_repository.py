# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from datetime import datetime
from typing import Dict, List, Optional, Union
from src.domain.entities import DataSource, SourceType
from src.interfaces.sources import ISourceRepository, ISourceStorage
from src.infrastructure.json_source_storage import JsonSourceStorage
from src.utils.logging_setup import get_logger

logger = get_logger("SourceRepository")


class SourceRepository(ISourceRepository):
    """
    Pure in-memory domain repository managing DataSources and topology associations.
    
    SOLID Architecture:
    - [SRP] Exclusively handles in-memory domain state of DataSources and associations.
    - [DIP] Relies on ISourceStorage protocol when optional persistence bridge is attached.
    - Pure domain: Free from UI frameworks (PyQt) and network I/O (requests/threading).
    """

    def __init__(self, storage: Optional[Union[ISourceStorage, str]] = None):
        if isinstance(storage, str):
            self._storage: Optional[ISourceStorage] = JsonSourceStorage(storage)
        else:
            self._storage = storage

        self._data_sources: Dict[str, DataSource] = {}
        self._associations: Dict[str, List[str]] = {}
        self._map_path: Optional[str] = None

        if self._storage is not None:
            self._load_from_storage()

    # =========================================================================
    # PUBLIC DOMAIN REPOSITORY API
    # =========================================================================

    def add(self, source: DataSource) -> None:
        """Register a new DataSource in the repository."""
        self._data_sources[source.id] = source
        if self._storage is not None:
            self._save_to_storage()

    def remove(self, source_id: str) -> Optional[DataSource]:
        """Remove a DataSource and clean up associated elements."""
        if source_id in self._data_sources:
            removed = self._data_sources.pop(source_id)
            for element_id in list(self._associations.keys()):
                if source_id in self._associations[element_id]:
                    self._associations[element_id].remove(source_id)
            if self._storage is not None:
                self._save_to_storage()
            return removed
        return None

    def get(self, source_id: str) -> Optional[DataSource]:
        """Find a DataSource by ID."""
        return self._data_sources.get(source_id)

    def get_all(self) -> List[DataSource]:
        """Retrieve all registered DataSources."""
        return list(self._data_sources.values())

    def update_value(self, source_id: str, value: float) -> None:
        """Update the latest telemetry value and timestamp for a DataSource."""
        source = self.get(source_id)
        if source:
            source.latest_value = value
            source.last_update = datetime.now().timestamp()

    def update_source(
        self,
        source_id: str,
        name: Optional[str] = None,
        is_local: Optional[bool] = None,
        source_type: Optional[SourceType] = None,
        connection_string: Optional[str] = None,
    ) -> Optional[DataSource]:
        """Update configurable properties of an existing DataSource."""
        source = self.get(source_id)
        if not source:
            return None
        if name is not None:
            source.name = name
        if is_local is not None:
            source.is_local = is_local
        if source_type is not None:
            source.source_type = source_type
        if connection_string is not None:
            source.connection_string = connection_string
        if self._storage is not None:
            self._save_to_storage()
        return source

    def associate(self, source_id: str, element_id: str) -> None:
        """Associate a source ID with a map topology element (node or edge). Restricted to local sources."""
        source = self.get(source_id)
        if source and not source.is_local:
            logger.debug(f"[SourceRepository] Ignored static association for global source '{source_id}' to element '{element_id}'.")
            return

        target = str(element_id).strip() if element_id else ""
        target_clean = target.lstrip("-")

        for eid in list(self._associations.keys()):
            # Keep opposite direction of the same road for bidirectional sensors; clear if moved to another road
            if not target or eid.lstrip("-") != target_clean:
                if source_id in self._associations[eid]:
                    self._associations[eid].remove(source_id)
                if not self._associations[eid]:
                    del self._associations[eid]

        if target:
            if target not in self._associations:
                self._associations[target] = []
            if source_id not in self._associations[target]:
                self._associations[target].append(source_id)

        if self._storage is not None:
            self._save_to_storage()

    def get_associations(self, element_id: str) -> List[str]:
        """Get source IDs associated with a given map element."""
        return self._associations.get(element_id, [])

    def get_element_for_source(self, source_id: str) -> Optional[str]:
        """Find the map element associated with a given source ID (local sources only)."""
        source = self.get(source_id)
        if source and not source.is_local:
            return None
        for element_id, sources in self._associations.items():
            if source_id in sources:
                return element_id
        return None

    def get_elements_for_source(self, source_id: str) -> List[str]:
        """Find all map elements associated with a given source ID (local sources only)."""
        source = self.get(source_id)
        if source and not source.is_local:
            return []
        elements = []
        for element_id, sources in self._associations.items():
            if source_id in sources:
                elements.append(element_id)
        return elements

    def toggle_origin(self, source_id: str) -> Optional[bool]:
        """Toggle a source between Local and Global scope."""
        source = self.get(source_id)
        if source:
            source.is_local = not source.is_local
            # If toggled to Global, strip any existing associations
            if not source.is_local:
                for eid in list(self._associations.keys()):
                    if source_id in self._associations[eid]:
                        self._associations[eid].remove(source_id)
                    if not self._associations[eid]:
                        del self._associations[eid]
            if self._storage is not None:
                self._save_to_storage()
            return source.is_local
        return None

    def get_next_source_id(self) -> str:
        """
        Generates the next monotonic source ID in the format 'src_{n}'.
        Scans all registered data sources to guarantee strict monotonic progression.
        """
        max_idx = 0
        for s in self._data_sources.values():
            if s.id.startswith("src_"):
                suffix = s.id[4:]
                num_str = ""
                for ch in suffix:
                    if ch.isdigit():
                        num_str += ch
                    else:
                        break
                if num_str:
                    try:
                        max_idx = max(max_idx, int(num_str))
                    except ValueError:
                        pass
        return f"src_{max_idx + 1}"

    def set_map_path(self, map_path: Optional[str]) -> None:
        """Sets the active map file path."""
        if self._map_path != map_path:
            self._map_path = map_path
            if self._storage is not None:
                self._save_to_storage()

    def get_map_path(self) -> Optional[str]:
        """Retrieves the persisted map file path."""
        return self._map_path

    def clear(self) -> None:
        """Resets all data sources, associations, and map path in memory."""
        self._data_sources.clear()
        self._associations.clear()
        self._map_path = None
        if self._storage is not None:
            self._save_to_storage()

    def save(self) -> None:
        """Persists current state to storage if attached."""
        if self._storage is not None:
            self._save_to_storage()

    def notify_source_updated(self, source: DataSource) -> None:
        """Persists updates to a data source."""
        self.save()

    def emit_restored_sources(self) -> None:
        """No-op on pure domain repository (implemented by reactive SourceManager)."""
        pass

    # =========================================================================
    # INTERNAL STORAGE DELEGATION
    # =========================================================================

    def _save_to_storage(self) -> None:
        if self._storage is not None:
            self._storage.save(self._data_sources, self._associations, self._map_path)

    def _load_from_storage(self) -> None:
        if self._storage is not None:
            sources, associations, map_path = self._storage.load()
            self._data_sources.update(sources)
            self._associations.update(associations)
            if map_path:
                self._map_path = map_path

            # Cleanse any legacy associations for non-local (global) sources
            cleaned = False
            for eid in list(self._associations.keys()):
                valid_local_sids = [
                    sid for sid in self._associations[eid]
                    if getattr(self._data_sources.get(sid), "is_local", True)
                ]
                if len(valid_local_sids) != len(self._associations[eid]):
                    cleaned = True
                if valid_local_sids:
                    self._associations[eid] = valid_local_sids
                else:
                    del self._associations[eid]

            if cleaned and self._storage is not None:
                self._save_to_storage()

# Re-export for backward compatibility
__all__ = ["SourceRepository", "JsonSourceStorage"]
