# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import torch
from typing import Dict, Any

# Import Core Domain
from src.domain.app_state import AppState
from src.domain.entities import SourceStatus

# Import SRP Components
from src.pipeline.ingestion_pipeline import IngestionPipeline
from src.managers.graph_manager import GraphManager
from src.managers.node_manager import NodeManager
from src.managers.storage_manager import StorageManager
from src.managers.xai_manager import XAIManager
from src.managers.kse_manager import KSEManager
from src.factories.node_factory import NodeFactory

# Import Infrastructure
from src.infrastructure.sensor_gateway import SensorGateway

# Import Workers
from src.workers.async_agents import AuditorWorker, LinguistWorker
from src.workers.xai_worker import XAIWorker

# Import Services
from src.services.historical_manager import HistoricalManager
from src.services.telemetry_service import TelemetryService
from src.factories.agent_factory import AgentFactory
from src.utils.logging_setup import get_logger

logger = get_logger("SystemBuilder")


class SystemBuilder:
    """
    Composite Builder responsible for assembling the entire runtime dependency graph.
    
    Refactored V4 (SOLID Architecture):
    - [SRP] Only handles object assembly and dependency wiring.
    - [DIP] Decoupled from concrete implementations via Factory/Container.
    """

    def __init__(self, app_state: AppState, device: torch.device, model_config: dict):
        self.app_state = app_state
        self.device = device
        self.config = model_config
        self.components: Dict[str, Any] = {}

    def build(self) -> Dict[str, Any]:
        """
        Main build sequence.
        Returns a dictionary containing all system components ready to run.
        """
        logger.info("🔨 Starting System Construction...")

        # 1. Base Services
        telemetry = TelemetryService()
        storage_manager = StorageManager()
        historical_manager = HistoricalManager(app_state=self.app_state)
        
        # 2. Spatial Context (Graph)
        map_nodes = self.app_state.get_all_nodes()
        map_edges = self.app_state.get_all_edges()
        
        # Fallback: create dummy nodes for sensors if no map loaded
        if not map_nodes and self.app_state.get_all_data_sources():
            from src.domain.entities import MapNode
            for src in self.app_state.get_all_data_sources():
                map_nodes.append(MapNode(id=src.id, x=0, y=0, node_type="sensor"))

        graph_manager = GraphManager(
            nodes=map_nodes,
            edges=map_edges,
            embedding_dim=32, # Default dim
            device=self.device
        )

        # 3. Node & Memory Manager (DIP: Injected Storage & Factory)
        node_manager = NodeManager(
            config=self.config,
            device=self.device,
            historical_manager=historical_manager,
            graph_manager=graph_manager,
            storage=storage_manager,
            node_factory=NodeFactory
        )

        # 4. Global Agents (Coordinator & Fuser)
        coordinator = None
        if map_nodes:
            coordinator = AgentFactory.create_coordinator(
                config=self.config,
                input_dim=32,
                hidden_dim=32,
                output_dim=32
            )
            coordinator.to(self.device)

        total_city_nodes = len(map_nodes) if map_nodes else max(1, len(self.app_state.get_all_data_sources()))
        fuser = AgentFactory.create_fuser(
            config=self.config,
            num_variates=total_city_nodes,
            seq_len=60, # Standard Synapse Seq Len
            pred_len=1
        )
        fuser.to(self.device)

        # 5. Workers (Async Threads)
        auditor_worker = AuditorWorker(input_dim=total_city_nodes)
        linguist_worker = LinguistWorker()
        xai_worker = XAIWorker(model_config=self.config)

        # 6. High-Level Managers (XAI, KSE, Pipeline)
        xai_manager = XAIManager(worker=xai_worker, app_state=self.app_state)
        
        ingestion_pipeline = IngestionPipeline(
            app_state=self.app_state,
            telemetry=telemetry
        )
        
        kse_manager = KSEManager(app_state=self.app_state)

        # 7. Infrastructure (Gateway)
        sensor_gateway = SensorGateway()

        # Pack everything
        self.components = {
            "telemetry": telemetry,
            "storage_manager": storage_manager,
            "historical_manager": historical_manager,
            "graph_manager": graph_manager,
            "node_manager": node_manager,
            "coordinator": coordinator,
            "fuser": fuser,
            "auditor_worker": auditor_worker,
            "linguist_worker": linguist_worker,
            "xai_worker": xai_worker,
            "xai_manager": xai_manager,
            "ingestion_pipeline": ingestion_pipeline,
            "kse_manager": kse_manager,
            "sensor_gateway": sensor_gateway
        }
        
        logger.info("✅ Construction Complete.")
        return self.components
