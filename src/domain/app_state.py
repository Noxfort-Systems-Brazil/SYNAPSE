# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from typing import Dict, List, Optional, Any

from src.domain.entities import MapNode, MapEdge, DataSource
from src.domain.topology_repository import TopologyRepository
from src.interfaces.topology import ITopologyRepository
from src.interfaces.interaction import IInteractionManager


class AppState(QObject):
    """
    Central Application State Facade / Orchestrator.
    
    SOLID Architecture:
    - [SRP] Coordinates sub-domain managers (Topology, Sources, UI Interaction) and central Qt signals.
    - [DIP] Injected with abstract protocols (ITopologyRepository, ISourceRepository/Manager, IInteractionManager).
    - [Encapsulation] Interacts with sub-managers through their public interface.
    """
    
    # Re-exposing Signals for application-wide reactivity
    map_data_loaded = pyqtSignal()
    association_mode_changed = pyqtSignal(bool)
    data_association_changed = pyqtSignal(str, str)
    data_source_added = pyqtSignal(DataSource)
    data_source_removed = pyqtSignal(str)
    source_origin_toggled = pyqtSignal(str, bool)

    def __init__(
        self,
        topology: Optional[ITopologyRepository] = None,
        sources: Optional[Any] = None,
        interaction: Optional[IInteractionManager] = None,
    ):
        super().__init__()
        
        # 1. Dependency Inversion Resolution with Sensible Defaults
        self.topology: ITopologyRepository = topology if topology is not None else TopologyRepository()
        
        if sources is not None:
            self.sources = sources
        else:
            # Lazy import to prevent circular or premature domain-to-manager dependencies
            from src.managers.source_manager import SourceManager
            self.sources = SourceManager()

        if interaction is not None:
            self.interaction: IInteractionManager = interaction
        else:
            from src.managers.interaction_manager import InteractionManager
            self.interaction: IInteractionManager = InteractionManager()
        
        # Restore persisted map path from source repository if available
        restored_map = self.sources.get_map_path()
        if restored_map:
            self.topology.set_map_file_path(restored_map)

        # Synchronization Flags
        self.is_meh_ready = False
        
        # 2. Wire Signals
        self._wire_signals()

    def _wire_signals(self) -> None:
        """Connects child events to central AppState signals."""
        for src_obj, sig_name, target_sig in [
            (self.topology, "map_loaded", self.map_data_loaded),
            (self.sources, "source_added", self.data_source_added),
            (self.sources, "source_removed", self.data_source_removed),
            (self.sources, "association_changed", self.data_association_changed),
            (self.sources, "source_origin_toggled", self.source_origin_toggled),
            (self.interaction, "mode_changed", self.association_mode_changed),
        ]:
            sig = getattr(src_obj, sig_name, None)
            if sig is not None:
                sig.connect(target_sig)

    # =========================================================================
    # TOPOLOGY DELEGATION METHODS
    # =========================================================================

    @pyqtSlot(list, list)
    def set_map_data(self, nodes_data: List[dict], edges_data: List[dict]):
        self.topology.load_data(nodes_data, edges_data)

    def set_map_source_path(self, path: str):
        self.topology.set_map_file_path(path)
        self.sources.set_map_path(path)

    def get_map_source_path(self) -> Optional[str]:
        return self.topology.get_map_file_path()

    def clear(self):
        """Resets topology, data sources, and interaction states."""
        self.topology.clear()
        self.sources.clear()
        self.interaction.exit_association_mode()

    def get_all_nodes(self) -> List[MapNode]:
        return self.topology.get_all_nodes()
    
    def get_all_edges(self) -> List[MapEdge]:
        return self.topology.get_all_edges()

    def get_node(self, node_id: str) -> Optional[MapNode]:
        return self.topology.get_node(node_id)

    def get_edge(self, edge_id: str) -> Optional[MapEdge]:
        return self.topology.get_edge(edge_id)

    # =========================================================================
    # SOURCE DELEGATION METHODS
    # =========================================================================
    
    def add_data_source(self, source: DataSource):
        self.sources.add(source)

    def emit_restored_sources(self):
        """Emit source_added for all pre-loaded sources (call AFTER UI signal wiring)."""
        self.sources.emit_restored_sources()

    def remove_data_source(self, source_id: str):
        self.sources.remove(source_id)

    def get_data_source(self, source_id: str) -> Optional[DataSource]:
        return self.sources.get(source_id)
    
    def get_all_data_sources(self) -> List[DataSource]:
        return self.sources.get_all()
    
    def get_source_by_device_id(self, device_id: str) -> Optional[DataSource]:
        return self.sources.get(device_id)

    def get_next_source_id(self) -> str:
        """Returns the next unique monotonic source ID."""
        return self.sources.get_next_source_id()

    def register_source(self, source: DataSource):
        self.add_data_source(source)
    
    def update_source_value(self, source_id: str, value: float):
        self.sources.update_value(source_id, value)

    def notify_source_updated(self, source: DataSource):
        """Notifies and persists updates to a data source."""
        self.sources.notify_source_updated(source)

    def toggle_source_origin(self, source_id: str):
        """Toggle source between Local and Global scope."""
        self.sources.toggle_origin(source_id)

    def update_data_source(
        self,
        source_id: str,
        name: Optional[str] = None,
        is_local: Optional[bool] = None,
        source_type: Optional[Any] = None,
        connection_string: Optional[str] = None,
    ) -> Optional[DataSource]:
        """Update configurable properties of a data source."""
        return self.sources.update_source(
            source_id=source_id,
            name=name,
            is_local=is_local,
            source_type=source_type,
            connection_string=connection_string,
        )

    # =========================================================================
    # INTERACTION & ASSOCIATION DELEGATION
    # =========================================================================

    @pyqtSlot(str)
    def enter_association_mode(self, source_id: str):
        self.interaction.enter_association_mode(source_id)
        
    @pyqtSlot()
    def exit_association_mode(self):
        self.interaction.exit_association_mode()

    def is_in_association_mode(self) -> bool:
        return bool(self.interaction.is_active)

    def associate(self, source_id: str, element_id: str) -> None:
        self.sources.associate(source_id, element_id)
    
    @pyqtSlot(str)
    def associate_selected_source_to_element(self, element_id: str):
        if not self.is_in_association_mode() or not self.interaction.selected_id:
            return
            
        source_id = self.interaction.selected_id
        self.sources.associate(source_id, element_id)
        self.exit_association_mode()

    def get_sources_associated_with_element(self, element_id: str) -> List[str]:
        return self.sources.get_associations(element_id)

    def get_element_for_source(self, source_id: str) -> Optional[str]:
        return self.sources.get_element_for_source(source_id)

    def get_elements_for_source(self, source_id: str) -> List[str]:
        return self.sources.get_elements_for_source(source_id)


# Backward-compatibility re-exports
__all__ = ["AppState", "TopologyRepository", "InteractionManager"]
