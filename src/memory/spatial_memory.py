# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import torch
import numpy as np
from typing import Dict, List, Tuple

class SpatialMemory:
    """
    Manages the spatial state of the network (Snapshot Buffer).
    
    Used by:
    - Coordinator Agent (GATv2 input).
    
    Responsibility:
    - Stores the latest known feature vector for every node (intersection) in the graph.
    - Assembles the 'Node Feature Matrix' (X) required by Graph Neural Networks.
    """

    def __init__(self, node_ids: List[str], feature_dim: int):
        """
        Args:
            node_ids: List of all intersection IDs in the managed region.
            feature_dim: Number of features per node.
        """
        self.node_ids = node_ids
        self.feature_dim = feature_dim
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Map node_id -> index (for matrix construction)
        self.id_to_idx = {nid: i for i, nid in enumerate(node_ids)}
        
        # Storage: [Num_Nodes, Features]
        # Initialize with zeros
        self.state_matrix = np.zeros((len(node_ids), feature_dim), dtype=np.float32)

    def update_node(self, node_id: str, features: List[float]):
        """
        Updates the state of a single node (e.g., when a sensor sends data).
        """
        if node_id in self.id_to_idx:
            idx = self.id_to_idx[node_id]
            self.state_matrix[idx] = np.array(features, dtype=np.float32)

    def get_node_features_tensor(self) -> torch.Tensor:
        """
        Returns the Node Feature Matrix (X) for the GAT.
        
        Returns:
            Tensor of shape [Num_Nodes, Features].
        """
        return torch.FloatTensor(self.state_matrix).to(self.device)

    def get_missing_nodes(self) -> List[str]:
        """
        Helper to identify nodes that haven't reported data yet (still zeros).
        (Heuristic: checks if row is all zeros).
        """
        missing = []
        for nid, idx in self.id_to_idx.items():
            if np.all(self.state_matrix[idx] == 0):
                missing.append(nid)
        return missing
