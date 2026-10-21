# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: src/managers/graph_manager.py
# Description: Pure Orchestrator for Graph Topology and Traffic Node State (SOLID / DDD / Clean Arch).

import time
import torch
from typing import List, Tuple, Dict, Optional, Any

from src.domain.app_state import AppState
from src.domain.entities import MapNode, MapEdge
from src.node.traffic_node import TrafficNode
from src.memory.spatial_memory import SpatialMemory
from src.services.historical_manager import HistoricalManager
from src.utils.logging_setup import get_logger

from src.managers.graph.node_factory import TrafficNodeFactory
from src.managers.graph.topology_builder import GraphTopologyBuilder
from src.managers.graph.payload_extractor import TelemetryPayloadExtractor
from src.managers.graph.element_resolver import SensorElementResolver
from src.managers.graph.hydrodynamics_engine import EdgeHydrodynamicsEngine
from src.managers.graph.global_feed_ingestor import GlobalJamsFeedIngestor

logger = get_logger("GraphManager")


class GraphManager:
    """
    Pure Orchestrator for Graph Topology and Traffic Node State.

    Coordinates:
    - Node factory creation (TrafficNodeFactory)
    - Connectivity tensor construction (GraphTopologyBuilder)
    - Sensor payload parsing & typing (TelemetryPayloadExtractor)
    - Sensor element association (SensorElementResolver)
    - Edge continuum physics calculation (EdgeHydrodynamicsEngine)
    """

    def __init__(
        self,
        app_state: AppState,
        embedding_dim: int = 64,
        device: torch.device = None,
        historical_manager: Optional[HistoricalManager] = None
    ):
        self.app_state = app_state
        self.embedding_dim = embedding_dim
        self.device = device if device else torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # Internal State
        self.nodes: Dict[str, TrafficNode] = {}
        self.spatial_memory: Optional[SpatialMemory] = None
        self.edge_index: Optional[torch.Tensor] = None
        self.edge_attr: Optional[torch.Tensor] = None
        self.ordered_node_ids: List[str] = []
        self.direct_edge_metrics: Dict[str, Dict[str, Any]] = {}
        self.edge_elements_map: Dict[str, Dict[str, Any]] = {}
        self.global_feed_ingestor = GlobalJamsFeedIngestor()

        if historical_manager is not None:
            self.historical_manager = historical_manager
        else:
            try:
                self.historical_manager = HistoricalManager(app_state)
            except TypeError:
                self.historical_manager = HistoricalManager()

        self.rebuild_graph()

    def rebuild_graph(self):
        """Syncs internal graph structures with AppState."""
        map_nodes = self.app_state.get_all_nodes()
        map_edges = self.app_state.get_all_edges()

        self.ordered_node_ids = [n.id for n in map_nodes]
        self.nodes = {
            mn.id: TrafficNodeFactory.create_traffic_node(
                map_node=mn,
                device=self.device,
                historical_manager=self.historical_manager,
                graph_manager=self
            )
            for mn in map_nodes
        }

        self.spatial_memory = SpatialMemory(self.ordered_node_ids, feature_dim=self.embedding_dim)
        edge_index, edge_attr = GraphTopologyBuilder.build_topology(map_nodes, map_edges, self.device)
        self.edge_index = edge_index
        self.edge_attr = edge_attr
        self.global_feed_ingestor.reset()
        logger.info(f"Graph Rebuilt: {len(self.nodes)} TrafficNodes Active.")

    def get_node(self, node_id: str) -> Optional[TrafficNode]:
        """Returns the active TrafficNode object (for XAI/TCN)."""
        return self.nodes.get(node_id)

    def get_ordered_node_ids(self) -> List[str]:
        """Returns the strict ordered list of Node IDs for tensor alignment."""
        return self.ordered_node_ids

    def _build_edge_index(self, nodes: List[MapNode], edges: List[MapEdge]) -> torch.Tensor:
        """Delegates edge index tensor construction to GraphTopologyBuilder."""
        return GraphTopologyBuilder.build_edge_index(nodes, edges, self.device)

    def get_graph_snapshot(self) -> Tuple[torch.Tensor, torch.Tensor]:
        """Returns current state tensors (x, edge_index) for GAT inference."""
        if not self.spatial_memory:
            return torch.empty(0), torch.empty(0)
        x = self.spatial_memory.get_node_features_tensor().to(self.device)
        return x, self.edge_index

    def update_node_memory(self, source_id: str, payload: Any, raw_payload: Any = None):
        """Injects sensor telemetry into corresponding Node or Edge memory."""
        source_obj = None
        get_ds_fn = getattr(self.app_state, "get_data_source", None)
        if callable(get_ds_fn):
            source_obj = get_ds_fn(source_id)
        else:
            get_all_ds_fn = getattr(self.app_state, "get_all_data_sources", None)
            if callable(get_all_ds_fn):
                for s in (get_all_ds_fn() or []):
                    if getattr(s, "id", None) == source_id:
                        source_obj = s
                        break

        # Fast-path for multi-segment global feeds (e.g., Waze jams list with per-street polylines & speeds)
        if (
            isinstance(raw_payload, dict)
            and "jams" in raw_payload
            and isinstance(raw_payload["jams"], list)
            and len(raw_payload["jams"]) > 0
        ):
            if self._ingest_global_jams_feed(source_id, source_obj, raw_payload["jams"]):
                return

        semantic_type = getattr(source_obj, "semantic_type", "") if source_obj else ""
        meta = getattr(source_obj, "metadata", {}) if (source_obj and isinstance(source_obj.metadata, dict)) else {}

        # 1. Parse & classify telemetry
        telemetry = TelemetryPayloadExtractor.extract(
            source_id=source_id,
            payload=payload,
            raw_payload=raw_payload,
            semantic_type=semantic_type,
            meta=meta
        )

        # 2. Resolve target elements (Nodes / Edges)
        element_ids = SensorElementResolver.resolve_source_elements(
            source_id=source_id,
            app_state=self.app_state,
            nodes=self.nodes,
            meta=meta,
            raw_payload=raw_payload
        )

        # 3. Propagate to resolved elements
        for element_id in element_ids:
            if element_id in self.nodes:
                self._update_direct_node(element_id, telemetry.value)
            else:
                self._update_edge_element(element_id, telemetry)

    def _ingest_global_jams_feed(self, source_id: str, source_obj: Any, jams: List[Any]) -> bool:
        """Unpacks multi-segment global feeds onto matched edges via GlobalJamsFeedIngestor."""
        return self.global_feed_ingestor.ingest(
            source_id=source_id,
            source_obj=source_obj,
            jams=jams,
            app_state=self.app_state,
            direct_edge_metrics=self.direct_edge_metrics,
            update_edge_fn=self._update_edge_element
        )

    def _update_direct_node(self, node_id: str, val: float):
        """Updates a junction node and its spatial embedding."""
        self.nodes[node_id].step(val)
        current_feats = [0.0] * self.embedding_dim
        current_feats[0] = val
        if self.spatial_memory:
            self.spatial_memory.update_node(node_id, current_feats)

    def _update_edge_element(self, element_id: str, telemetry: Any):
        """Resolves edge kinematics and updates edge metrics and boundary junctions."""
        target_edge = self._resolve_target_edge(element_id)
        if not target_edge:
            return

        speed_val, density_val = EdgeHydrodynamicsEngine.compute_edge_kinetics(
            target_edge=target_edge,
            val=telemetry.value,
            is_speed_sensor=telemetry.is_speed_sensor,
            is_flow_sensor=telemetry.is_flow_sensor,
            is_count_sensor=telemetry.is_count_sensor,
            measured_speed_ms=telemetry.measured_speed_ms
        )

        metric_entry = {
            "value": telemetry.value,
            "speed": speed_val,
            "density": density_val,
            "timestamp": time.time()
        }
        self.direct_edge_metrics[target_edge.id] = metric_entry
        self.direct_edge_metrics[element_id] = metric_entry

        edge_map = getattr(self, "edge_elements_map", None)
        if isinstance(edge_map, dict):
            if target_edge.id in edge_map:
                edge_map[target_edge.id]["speed"] = speed_val
                edge_map[target_edge.id]["density"] = density_val
            if element_id in edge_map:
                edge_map[element_id]["speed"] = speed_val
                edge_map[element_id]["density"] = density_val

        # Propagate physical continuum density to connected junctions
        if target_edge.from_node in self.nodes:
            self._update_direct_node(target_edge.from_node, density_val)
        if target_edge.to_node in self.nodes:
            self._update_direct_node(target_edge.to_node, density_val)

    def _resolve_target_edge(self, element_id: str) -> Optional[MapEdge]:
        """Looks up or constructs target MapEdge from AppState."""
        target_edge = None
        get_edge_fn = getattr(self.app_state, "get_edge", None)
        if callable(get_edge_fn):
            target_edge = get_edge_fn(element_id)

        get_all_edges_fn = getattr(self.app_state, "get_all_edges", None)
        if not target_edge and callable(get_all_edges_fn):
            clean_id = element_id.lstrip("-")
            for e in get_all_edges_fn():
                if e.id == element_id or e.id.lstrip("-") == clean_id:
                    target_edge = e
                    break

        edge_map = getattr(self, "edge_elements_map", None)
        if not target_edge and isinstance(edge_map, dict) and element_id in edge_map:
            info = edge_map[element_id]
            target_edge = MapEdge(
                id=element_id,
                from_node=info.get("from", ""),
                to_node=info.get("to", ""),
                shape=[],
                max_speed=info.get("speed", 13.89),
                lanes=info.get("lanes", 1),
                length=info.get("length", 100.0)
            )

        return target_edge
