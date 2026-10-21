# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: src/services/map_service.py
# Description: Pure Application Service Orchestrator for Network Topology (Clean Architecture).

import os
from urllib.parse import unquote, urlparse
from pathlib import Path
from typing import List, Dict, Optional
from PyQt6.QtCore import QObject, pyqtSignal

from src.logging.facade import get_logger
from src.domain.entities import MapNode, MapEdge
from src.services.map.sumo_network_parser import SumoNetworkParser


class MapService(QObject):
    """
    Pure Orchestrator for Network Topology (The Cartographer of Synapse).

    Coordinates:
    - Path normalization and validation
    - Delegation to SumoNetworkParser (SRP)
    - Population of domain entities (MapNode & MapEdge)
    - PyQt signal notification for map consumers
    """

    # Signals
    map_loaded = pyqtSignal(int, int)  # (num_nodes, num_edges)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.logger = get_logger("MapService")
        self.nodes: List[MapNode] = []
        self.edges: List[MapEdge] = []
        self._node_lookup: Dict[str, MapNode] = {}
        self.last_error: Optional[str] = None

    def load_network(self, file_path: str) -> bool:
        """Parses a SUMO network file and populates the domain entities."""
        self.last_error = None

        if not file_path or not str(file_path).strip():
            msg = "Caminho do arquivo de rede viária não foi informado."
            self.logger.error(f"[MapService] ❌ {msg}")
            self.last_error = msg
            self.error_occurred.emit(msg)
            return False

        # Clean and normalize path (handle file:// URL, %20 encoding, ~, quotes)
        clean_path_str = str(file_path).strip().strip('"\'')
        if clean_path_str.startswith("file://"):
            clean_path_str = unquote(urlparse(clean_path_str).path)
        clean_path_str = unquote(clean_path_str)
        clean_path_str = os.path.expanduser(clean_path_str)

        path = Path(clean_path_str).resolve()
        if not path.exists():
            msg = f"Arquivo de mapa não encontrado no disco: {clean_path_str}"
            self.logger.error(f"[MapService] ❌ {msg}")
            self.last_error = msg
            self.error_occurred.emit(msg)
            return False

        self.logger.info(f"[MapService] 🗺️ Carregando Topologia SUMO de: '{path}'...")

        try:
            parsed = SumoNetworkParser.parse(path)
            self.nodes = parsed.nodes
            self.edges = parsed.edges
            self._node_lookup = parsed.node_lookup

            self.logger.info(f"[MapService] 🚀 Malha Carregada: {len(self.nodes)} nós e {len(self.edges)} vias.")
            self.map_loaded.emit(len(self.nodes), len(self.edges))
            return True

        except Exception as e:
            msg = str(e)
            self.logger.error(f"[MapService] ❌ Falha ao processar arquivo SUMO: {msg}")
            self.last_error = msg
            self.error_occurred.emit(msg)
            return False
