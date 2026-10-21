# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: src/managers/graph/node_factory.py
# Description: Factory for assembling TrafficNode aggregates and neural agents (SOLID: SRP/DIP).

from typing import Dict, Any, Optional
import torch

from src.domain.entities import MapNode
from src.node.traffic_node import TrafficNode
from src.memory.temporal_memory import TemporalMemory
from src.agents.specialist_agent import SpecialistAgent
from src.kse.filter import RobustKalmanFilter
from src.kse.definitions import PROFILES
from src.services.historical_manager import HistoricalManager


class TrafficNodeFactory:
    """Assembles and wires TrafficNode instances with local agents and memories."""

    @staticmethod
    def create_traffic_node(
        map_node: MapNode,
        device: torch.device,
        historical_manager: Optional[HistoricalManager],
        graph_manager: Any
    ) -> TrafficNode:
        # A. Memory Buffer
        mem = TemporalMemory(feature_dim=1, max_len=60)

        # B. Specialist Neural Agent (TCN)
        agent = SpecialistAgent(input_dim=1, output_dim=32, num_channels=[16, 32])
        agent.to(device)
        agent.freeze()

        # C. Physics Engine / Kalman Filter
        profile = PROFILES["DEFAULT"]
        if "cam" in map_node.id.lower():
            profile = PROFILES["CAMERA"]
        elif "loop" in map_node.id.lower():
            profile = PROFILES["INDUCTIVE"]

        kse = RobustKalmanFilter(node_id=map_node.id, initial_val=0.0, profile=profile)

        # D. Assemble TrafficNode
        return TrafficNode(
            source_id=map_node.id,
            memory=mem,
            agent=agent,
            historical_manager=historical_manager,
            physics_engine=kse,
            graph_manager=graph_manager
        )
