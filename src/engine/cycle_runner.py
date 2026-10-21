# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import numpy as np
import torch
from typing import Dict, Optional, Any, Union

from src.interfaces.node import INodeManager
# Import Managers and Agents for type hinting
from src.managers.node_manager import NodeManager
from src.managers.graph_manager import GraphManager
from src.managers.kse_manager import KSEManager
from src.agents.coordinator_agent import CoordinatorAgent
from src.agents.fuser_agent import FuserAgent
from src.workers.async_agents import AuditorWorker

class CycleRunner:
    """
    Encapsulates the 'Thinking Process' of the SYNAPSE system.
    
    Responsibility:
    - Executes the synchronous control loop (~1Hz).
    - Coordinates the interaction between GAT (Spatial), Fuser (Temporal), and KSE (Physics).
    - Returns a results dictionary for the Engine to emit/log.
    
    This separation allows the InferenceEngine to focus on Event Orchestration 
    rather than algorithmic logic.
    """

    def __init__(self):
        self.results: Dict[str, Any] = {}

    def execute_cycle(
        self,
        node_manager: Optional[Union[INodeManager, NodeManager]],
        graph_manager: Optional[GraphManager],
        kse_manager: Optional[KSEManager],
        coordinator: Optional[CoordinatorAgent],
        fuser: Optional[FuserAgent],
        auditor_worker: Optional[AuditorWorker]
    ) -> Dict[str, Any]:
        """
        Runs one iteration of the global intelligence loop.
        
        Args:
            node_manager: Holds the state of all traffic nodes.
            graph_manager: Manages the spatial graph topology.
            kse_manager: The Kinetic State Engine for physics synchronization.
            coordinator: The GATv2 agent for spatial reasoning.
            fuser: The Transformer agent for temporal forecasting.
            auditor_worker: The worker responsible for safety checks on predictions.
            
        Returns:
            A dictionary containing metadata about the cycle execution (e.g., shapes, status).
        """
        self.results = {}
        
        if not node_manager:
            return self.results

        # 1. Spatial Logic (Coordinator Agent / GAT)
        # Processes the graph to understand intersection dependencies
        if graph_manager and coordinator:
            x, edge_index = graph_manager.get_graph_snapshot()
            # Only process if graph is valid (has nodes and edges)
            if x.size(0) > 0 and edge_index.size(1) > 0:
                # Coordinator updates the latent state of nodes in place or via manager
                coordinator.process_region(x, edge_index)

        # 2. Temporal Logic & Physics Sync (Fuser + KSE)
        if fuser:
            active_ids = node_manager.get_ready_nodes_ids()
            nodes_dict = node_manager.get_all_nodes()
            
            # 2a. Prepare Reality Snapshot for KSE (Physics Engine)
            reality_snapshot = {}
            active_histories = []
            
            for nid in active_ids:
                node = nodes_dict[nid]
                # Collect history for Fuser
                active_histories.append(node.memory.get_numpy().squeeze(-1))
                
                # Extract scalar state for Physics (Reality Blending)
                reality_snapshot[nid] = {
                    "value": node.last_value,
                    # If we had velocity sensor data, we would pass it here. 
                    # For now, KSE derives it or uses 0.0 as baseline.
                    "velocity": 0.0 
                }
            
            # 2b. Sync KSE with this new Reality Frame
            if kse_manager and reality_snapshot:
                kse_manager.sync_with_reality(reality_snapshot)

            # 2c. Run Fuser Forecast (The Future Prediction)
            if active_histories:
                try:
                    # Stack histories: [Batch, Seq_Len]
                    global_history = np.stack(active_histories, axis=1)
                    
                    # Predict: [Batch, Pred_Len]
                    forecast = fuser.predict_state(global_history)
                    
                    # Log shape for debugging/dashboard
                    self.results["fuser_forecast_shape"] = list(forecast.shape)
                    
                    # 2d. Audit the Prediction (Safety Check)
                    if auditor_worker:
                        # Take the first prediction step of the first batch for quick audit
                        # In a full system, we would audit the whole tensor.
                        next_state_vector = forecast[0, :]
                        auditor_worker.submit_state(next_state_vector)
                        
                except Exception as e:
                    # Log internally or pass error in results
                    self.results["cycle_error"] = str(e)
                    pass

        return self.results
