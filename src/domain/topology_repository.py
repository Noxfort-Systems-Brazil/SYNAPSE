# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from PyQt6.QtCore import QObject, pyqtSignal
from typing import Dict, List, Optional
from src.domain.entities import MapNode, MapEdge


class TopologyRepository(QObject):
    """
    Pure domain repository managing static map topology (Nodes, Edges, Road Geometry).
    
    SOLID Architecture:
    - [SRP] Exclusively handles in-memory static map entities (The 'World').
    - [DIP] Satisfies ITopologyRepository and ITopologyReader protocols structurally.
    - [Encapsulation] Exposes proper accessors for map_file_path rather than internal private fields.
    """
    map_loaded = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._nodes: Dict[str, MapNode] = {}
        self._edges: Dict[str, MapEdge] = {}
        self._map_file_path: Optional[str] = None

    def load_data(self, nodes_data: List[dict], edges_data: List[dict]) -> None:
        """Hydrates MapNode and MapEdge domain entities from raw dictionaries."""
        self._nodes.clear()
        self._edges.clear()
        
        # Hydrate MapNode entities
        for n_data in nodes_data:
            node = MapNode(
                id=n_data['id'], 
                x=n_data['x'], 
                y=n_data['y'], 
                node_type=n_data['type'],
                real_name=n_data.get('name'),
                tl_logic_id=n_data.get('tl_logic_id')
            )
            self._nodes[n_data['id']] = node

        # Hydrate MapEdge entities
        for e_data in edges_data:
            src = e_data.get('from_node')
            dst = e_data.get('to_node')
            if not src or not dst:
                src = e_data.get('from', "N/A")
                dst = e_data.get('to', "N/A")

            edge = MapEdge(
                id=e_data['id'], 
                from_node=src, 
                to_node=dst, 
                shape=e_data['shape'],
                real_name=e_data.get('name'),
                weight=float(e_data.get('weight', e_data.get('length', 1.0))),
                length=float(e_data.get('length', 100.0)),
                max_speed=float(e_data.get('max_speed', 13.89)),
                lanes=int(e_data.get('lanes', 1)),
                edge_type=str(e_data.get('edge_type', e_data.get('type', 'highway.residential'))),
                priority=int(e_data.get('priority', 1)),
                signal_group_id=e_data.get('signal_group_id')
            )
            self._edges[e_data['id']] = edge
        
        self.map_loaded.emit()

    def clear(self) -> None:
        """Clears all nodes, edges, and the active map file path."""
        self._nodes.clear()
        self._edges.clear()
        self._map_file_path = None
        self.map_loaded.emit()

    def get_all_nodes(self) -> List[MapNode]:
        return list(self._nodes.values())
    
    def get_all_edges(self) -> List[MapEdge]:
        return list(self._edges.values())

    def get_node(self, node_id: str) -> Optional[MapNode]:
        return self._nodes.get(node_id)

    def get_edge(self, edge_id: str) -> Optional[MapEdge]:
        return self._edges.get(edge_id)

    def get_map_file_path(self) -> Optional[str]:
        """Returns the active map file path."""
        return self._map_file_path

    def set_map_file_path(self, path: Optional[str]) -> None:
        """Sets the active map file path."""
        self._map_file_path = path

    # Backward compatibility property for direct access
    @property
    def map_file_path(self) -> Optional[str]:
        return self._map_file_path

    @map_file_path.setter
    def map_file_path(self, value: Optional[str]) -> None:
        self._map_file_path = value


__all__ = ["TopologyRepository"]
