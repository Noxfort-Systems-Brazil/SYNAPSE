# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

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

        # B. Specialist Neural Agent (TCN) — Lazily instantiated per active/historical sensor
        def _build_isolated_agent() -> SpecialistAgent:
            agent = SpecialistAgent(input_dim=1, output_dim=32, num_channels=[16, 32])
            agent.to(device)
            agent.freeze()
            return agent

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
            agent=None,
            agent_factory=_build_isolated_agent,
            output_dim=32,
            historical_manager=historical_manager,
            physics_engine=kse,
            graph_manager=graph_manager
        )
