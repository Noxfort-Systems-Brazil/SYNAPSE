# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import numpy as np
import logging
from typing import Dict, Any

# --- Domain Imports ---
from src.domain.app_state import AppState
from src.managers.graph_manager import GraphManager

class SnapshotBuilder:
    """
    Responsible for constructing the Global Network Snapshot.
    
    Refactored V4 (Architecture Fix — No Duplicate TCN):
    - Reads `traffic_node.last_embedding` instead of running TCN again.
    - TrafficNode.step() / ghost_step() already compute the TCN embedding.
    - This class only COLLECTS the cached results into a snapshot dict.
    """

    def __init__(self, app_state: AppState, graph_manager: GraphManager, embedding_dim: int = 32):
        self.logger = logging.getLogger(__name__)
        self.app_state = app_state
        self.graph_manager = graph_manager
        self.embedding_dim = embedding_dim
        self._zero_embedding = np.zeros(self.embedding_dim, dtype=np.float32)
        self._zero_embedding.flags.writeable = False
        
    def gather_snapshot(self) -> Dict[str, Any]:
        """
        Iterates over all nodes to build a complete state snapshot for the cycle.
        
        Architecture Fix: Uses the CACHED embedding from TrafficNode
        (computed by step() or ghost_step()) instead of re-running TCN.
        
        Returns:
            Dict mapping NodeID -> {embedding, value, timestamp}
        """
        snapshot = {}
        
        # Get static nodes from AppState (The Source of Truth for Topology)
        map_nodes = self.app_state.get_all_nodes()
        
        for map_node in map_nodes:
            # Retrieve the RUNTIME TrafficNode from GraphManager using ID
            traffic_node = self.graph_manager.get_node(map_node.id)
            
            # Determine whether this node has active physical sensor reality
            is_node_real = False
            if traffic_node:
                is_node_real = bool(
                    (traffic_node.is_validated or traffic_node.steps_processed > 0)
                    and getattr(traffic_node, "fallback_steps", 0) <= 75
                    and traffic_node.last_value > 0.0
                )

            # Prepare default payload using pre-allocated read-only zero vector
            payload = {
                "embedding": self._zero_embedding,
                "value": 0.0,
                "timestamp": 0.0,
                "type": "real" if is_node_real else "synthetic",
                "status": "Active" if is_node_real else "Ghost"
            }
            
            # If GraphManager hasn't initialized this node yet, use the default
            if not traffic_node:
                snapshot[map_node.id] = payload
                continue

            try:
                # Architecture Fix: Read CACHED embedding (already computed by step/ghost_step)
                payload["embedding"] = traffic_node.last_embedding
                payload["value"] = traffic_node.last_value
                payload["timestamp"] = traffic_node.last_timestamp
                
                # Fetch recent Physics (Kalman Filter State) for Dead Reckoning extrapolation
                kse_snap = traffic_node.kse.get_kinetic_snapshot()
                payload["physics"] = {
                    "v": kse_snap.v,
                    "a": kse_snap.a
                }
                
                snapshot[traffic_node.source_id] = payload
                
            except Exception as e:
                snapshot[traffic_node.source_id] = payload

        # Inject direct edge telemetry from associated sensors if available
        direct_metrics = getattr(self.graph_manager, "direct_edge_metrics", None)
        if isinstance(direct_metrics, dict) and direct_metrics:
            for edge_id, edge_metric in direct_metrics.items():
                snapshot[edge_id] = edge_metric
                
        return snapshot
