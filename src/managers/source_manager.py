# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from PyQt6.QtCore import QObject, pyqtSignal
from typing import Dict, List, Optional, Union

from src.domain.entities import DataSource, SourceType
from src.domain.source_repository import SourceRepository
from src.infrastructure.json_source_storage import JsonSourceStorage
from src.services.source_probe_service import HttpSourceProbeService
from src.interfaces.sources import ISourceRepository, ISourceStorage, ISourceProbeService
from src.utils.logging_setup import get_logger

logger = get_logger("SourceManager")


class SourceManager(QObject):
    """
    Application Facade / Orchestrator for DataSource lifecycle, persistence, and UI events.
    
    SOLID Architecture:
    - [SRP] Coordinates data repository, persistence storage, probe service, and Qt signals.
    - [DIP] Injected with abstract protocols (ISourceRepository, ISourceStorage, ISourceProbeService).
    - [OCP] Extensible without modifying orchestration logic.
    """

    source_added = pyqtSignal(DataSource)
    source_removed = pyqtSignal(str)
    association_changed = pyqtSignal(str, str)
    source_origin_toggled = pyqtSignal(str, bool)

    def __init__(
        self,
        repository: Optional[ISourceRepository] = None,
        storage: Optional[Union[ISourceStorage, str]] = None,
        probe_service: Optional[ISourceProbeService] = None,
    ):
        super().__init__()
        
        # 1. Dependency Inversion Resolution
        self.repository = repository if repository is not None else SourceRepository()
        
        if isinstance(storage, str):
            self.storage: ISourceStorage = JsonSourceStorage(storage)
        elif storage is not None:
            self.storage = storage
        else:
            self.storage = JsonSourceStorage()

        self.probe_service = probe_service if probe_service is not None else HttpSourceProbeService()

        self._map_path: Optional[str] = None

        # 2. Restore pre-saved state from disk
        self._load_from_storage()

    # --- Backward compatibility accessors for internal collections ---
    @property
    def _data_sources(self) -> Dict[str, DataSource]:
        ds = getattr(self.repository, "_data_sources", None)
        if ds is not None:
            return ds
        return {s.id: s for s in self.repository.get_all()}

    @property
    def _associations(self) -> Dict[str, List[str]]:
        assoc = getattr(self.repository, "_associations", None)
        return assoc if assoc is not None else {}

    # =========================================================================
    # PUBLIC ORCHESTRATION API
    # =========================================================================

    def add(self, source: DataSource):
        """Orchestrates adding a source: repository insert -> Qt emit -> persist -> probe."""
        self.repository.add(source)
        self.source_added.emit(source)
        self._save_to_storage()

        # Terminal Visual Feedback
        src_type_desc = "LOCAL (PUSH - Porta 8080)" if source.is_local else "GLOBAL (PULL - API Externa)"
        status_desc = getattr(source.status, "value", str(source.status))
        logger.info(
            f"📝 Sensor Cadastrado: ID='{source.id}' | Nome='{source.name}' | "
            f"Origem='{src_type_desc}' | Status Inicial='{status_desc}'"
        )

        # Delegate health check probe to probe service
        self.probe_service.probe(source)

    def remove(self, source_id: str):
        """Orchestrates removing a source: repository delete -> Qt emit -> persist."""
        removed = self.repository.remove(source_id)
        if removed:
            self.source_removed.emit(source_id)
            self._save_to_storage()
            logger.info(f"🗑️ Sensor Removido do Sistema: ID='{source_id}' (Nome='{removed.name}')")

    def get(self, source_id: str) -> Optional[DataSource]:
        return self.repository.get(source_id)

    def get_all(self) -> List[DataSource]:
        return self.repository.get_all()

    def update_value(self, source_id: str, value: float):
        self.repository.update_value(source_id, value)

    def associate(self, source_id: str, element_id: str):
        self.repository.associate(source_id, element_id)
        self.association_changed.emit(source_id, element_id)
        self._save_to_storage()

    def get_associations(self, element_id: str) -> List[str]:
        return self.repository.get_associations(element_id)

    def get_element_for_source(self, source_id: str) -> Optional[str]:
        return self.repository.get_element_for_source(source_id)

    def get_elements_for_source(self, source_id: str) -> List[str]:
        return self.repository.get_elements_for_source(source_id)

    def toggle_origin(self, source_id: str):
        """Toggle source between Local and Global scope, persist and emit signal."""
        new_is_local = self.repository.toggle_origin(source_id)
        if new_is_local is not None:
            self._save_to_storage()
            self.source_origin_toggled.emit(source_id, new_is_local)

    def update_source(
        self,
        source_id: str,
        name: Optional[str] = None,
        is_local: Optional[bool] = None,
        source_type: Optional[SourceType] = None,
        connection_string: Optional[str] = None,
    ) -> Optional[DataSource]:
        """Updates source attributes, persists to storage, and notifies subscribers."""
        src = self.repository.update_source(
            source_id=source_id,
            name=name,
            is_local=is_local,
            source_type=source_type,
            connection_string=connection_string,
        )
        if src:
            self._save_to_storage()
            self.source_added.emit(src)
        return src

    def get_next_source_id(self) -> str:
        return self.repository.get_next_source_id()

    def set_map_path(self, map_path: Optional[str]):
        """Sets the active map file path and persists to storage."""
        if self._map_path != map_path:
            self._map_path = map_path
            self._save_to_storage()

    def get_map_path(self) -> Optional[str]:
        """Retrieves the persisted map file path."""
        return self._map_path

    def clear(self):
        """Resets all data sources, associations, and map path."""
        self.repository.clear()
        self._map_path = None
        self._save_to_storage()

    def emit_restored_sources(self):
        """Emit source_added for all pre-loaded sources (call AFTER UI signal wiring)."""
        for source in self.repository.get_all():
            self.source_added.emit(source)

    def save(self):
        """Persists current data sources and associations to storage."""
        self._save_to_storage()

    def notify_source_updated(self, source: DataSource):
        """Emits source_added signal for the updated source and persists changes."""
        self.source_added.emit(source)
        self._save_to_storage()

    # =========================================================================
    # INTERNAL PERSISTENCE DELEGATION
    # =========================================================================

    def _save_to_storage(self):
        sources_dict = {s.id: s for s in self.repository.get_all()}
        associations_dict = self._associations
        self.storage.save(sources_dict, associations_dict, self._map_path)

    def _load_from_storage(self):
        sources, associations, map_path = self.storage.load()
        for s in sources.values():
            self.repository.add(s)
        repo_assoc = getattr(self.repository, "_associations", None)
        if repo_assoc is not None:
            repo_assoc.update(associations)
        if map_path:
            self._map_path = map_path

