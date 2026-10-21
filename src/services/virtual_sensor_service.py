# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: src/services/virtual_sensor_service.py
# Description: Pure Orchestrator for Virtual Sensor Fallbacks (SOLID / Clean Arch).

from typing import Any, Dict, List, Optional, Set, Tuple
from PyQt6.QtCore import QObject, pyqtSignal

from src.domain.entities import DataSource, MapEdge, SourceStatus, SourceType
from src.domain.app_state import AppState
from src.factories.agent_factory import AgentFactory
from src.agents.specialist_agent import SpecialistAgent
from src.utils.logging_setup import get_logger

# Delegated Resolvers & Imputers (SRP)
from src.services.virtual_sensor.topology_neighbor_resolver import TopologyNeighborResolver
from src.services.virtual_sensor.traffic_imputer import VirtualTrafficImputer

logger = get_logger("VirtualSensorService")


class VirtualSensorService(QObject):
    """
    Virtual Sensor Fallback via Nearest Neighbor in SUMO Topology (Pure Orchestrator).

    Coordinates:
    - Active physical sensor detection
    - Delegation to TopologyNeighborResolver (SRP)
    - Delegation to VirtualTrafficImputer (SRP)
    - Virtual sensor entity and SpecialistAgent lifecycle
    - Signal emissions for telemetry updates
    """

    virtual_sensor_created = pyqtSignal(str, str)  # (source_id, edge_id)
    telemetry_updated = pyqtSignal(str, dict)       # (edge_id, values)

    def __init__(
        self,
        app_state: AppState,
        agent_factory: Optional[AgentFactory] = None,
        historical_manager: Optional[Any] = None
    ):
        super().__init__()
        self.app_state = app_state
        self.agent_factory = agent_factory or AgentFactory()
        self.historical_manager = historical_manager
        self.virtual_sources: Dict[str, DataSource] = {}

    def get_active_edge_ids(self) -> Set[str]:
        """Identifies all edge IDs currently observed by an ACTIVE physical sensor."""
        active_edges = set()
        all_sources = self.app_state.get_all_data_sources() or []
        for source in all_sources:
            if source.status == SourceStatus.ACTIVE and not source.metadata.get("is_virtual", False):
                edge_id = self.app_state.get_element_for_source(source.id)
                if not edge_id and source.metadata:
                    edge_id = source.metadata.get("edge_id")
                if edge_id:
                    active_edges.add(edge_id)
        return active_edges

    def find_nearest_active_edge(
        self,
        target_edge: MapEdge,
        all_edges: List[MapEdge],
        active_edge_ids: Set[str]
    ) -> Optional[Tuple[MapEdge, str, float]]:
        return TopologyNeighborResolver.find_nearest_active_edge(
            target_edge, all_edges, active_edge_ids
        )

    def impute_traffic_for_edge(
        self,
        target_edge: MapEdge,
        all_edges: List[MapEdge],
        active_edge_ids: Set[str]
    ) -> Dict[str, Any]:
        return VirtualTrafficImputer.impute_traffic_for_edge(
            target_edge=target_edge,
            all_edges=all_edges,
            active_edge_ids=active_edge_ids,
            app_state=self.app_state
        )

    def create_or_get_virtual_sensor(self, target_edge_id: str) -> Tuple[DataSource, SpecialistAgent]:
        """Creates or retrieves a virtual sensor for an edge and wires its SpecialistAgent."""
        source_id = f"virt_{target_edge_id}"

        source = self.app_state.get_data_source(source_id)
        if source is None:
            source = DataSource(
                id=source_id,
                name=f"Virtual Sensor ({target_edge_id})",
                source_type=SourceType.API,
                is_local=True,
                status=SourceStatus.ACTIVE,
                semantic_type="Vehicle Flow",
                inferred_unit="veh/s",
                confidence_score=0.85,
                metadata={"is_virtual": True, "edge_id": target_edge_id}
            )
            self.app_state.add_data_source(source)
            sources_repo = getattr(self.app_state, "sources", None)
            assoc_fn = getattr(sources_repo, "associate", None)
            if callable(assoc_fn):
                assoc_fn(source_id, target_edge_id)

            self.virtual_sources[source_id] = source
            logger.info(f"✨ [VirtualSensor] Created virtual sensor '{source_id}' on edge '{target_edge_id}'.")
            self.virtual_sensor_created.emit(source_id, target_edge_id)

        specialist = self.agent_factory.get_or_create_specialist(source_id)
        specialist.target_edge_id = target_edge_id
        specialist.semantic_type = "Vehicle Flow"
        specialist.inferred_unit = "veh/s"

        return source, specialist

    def sync_virtual_sensors(self) -> Dict[str, Dict[str, float]]:
        """Scans all SUMO edges, maintaining virtual sensors for unobserved segments."""
        all_edges = self.app_state.get_all_edges()
        if not all_edges:
            return {}

        active_edges = self.get_active_edge_ids()
        results: Dict[str, Dict[str, float]] = {}

        for edge in all_edges:
            if edge.id not in active_edges:
                imputed = self.impute_traffic_for_edge(edge, all_edges, active_edges)
                source, _ = self.create_or_get_virtual_sensor(edge.id)
                source.latest_value = imputed["flow_vps"]
                self.telemetry_updated.emit(edge.id, imputed)
                results[edge.id] = imputed

        return results
