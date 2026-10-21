# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Any, List, Optional, Tuple
import numpy as np
import logging

from src.interfaces.quarantine import ISensorPhysicsValidator, ISemanticClassifier
from src.services.semantic_classifier import SemanticClassifier
from src.domain.entities import DataSource, MapEdge
from src.physics.traffic_symbolic_rules import (
    DEFAULT_CAPACITY_PER_LANE_VEH_H,
    SATURATION_FLOW_RATE_PER_SEC,
    DEFAULT_JAM_DENSITY_PER_LANE,
    DEFAULT_URBAN_SPEED_LIMIT_KMH,
    MAX_URBAN_SPEED_CEILING_KMH,
    MAX_VEHICLE_ACCEL_MS2,
    TrafficSymbolicRules,
)

logger = logging.getLogger("Synapse.Physics.SensorPhysicalValidator")

__all__ = [
    "DEFAULT_CAPACITY_PER_LANE_VEH_H",
    "SATURATION_FLOW_RATE_PER_SEC",
    "DEFAULT_JAM_DENSITY_PER_LANE",
    "DEFAULT_URBAN_SPEED_LIMIT_KMH",
    "MAX_URBAN_SPEED_CEILING_KMH",
    "MAX_VEHICLE_ACCEL_MS2",
    "SensorPhysicalValidator",
]


class SensorPhysicalValidator(ISensorPhysicsValidator):
    """
    Validates physical consistency and macroscopic traffic invariants
    using context-aware symbolic rules derived from roadway topology, sampling delta-time (dt),
    engineering units, and Neuro-PINN residual inference.
    """

    def __init__(
        self,
        semantic_classifier: Optional[ISemanticClassifier] = None,
        max_physical_bound: float = 10000.0,
        max_physics_residual: float = 0.5,
        app_state: Optional[Any] = None
    ):
        self.semantic_classifier = semantic_classifier or SemanticClassifier()
        self.max_physical_bound = max_physical_bound
        self.max_physics_residual = max_physics_residual
        self.app_state = app_state

    def validate(
        self,
        source: DataSource,
        data_np: np.ndarray,
        data_chunk: Optional[List[Any]] = None,
        agent: Optional[Any] = None,
        app_state: Optional[Any] = None
    ) -> bool:
        """
        Uses Modality, Topology Context, Sampling dt, and PINN Agent to validate physical feasibility.
        """
        if len(data_np) == 0:
            logger.warning(f"⚠️ [Physics] Violação: Nenhum valor numérico válido encontrado nas amostras de '{source.name}'.")
            return False

        active_app_state = app_state or self.app_state
        sem_type, unit, _ = self.semantic_classifier.classify(source, data_np, data_chunk)
        sem_lower = sem_type.lower()

        # 1. Fundamental Non-Negativity Invariant
        if np.min(data_np) < 0:
            logger.warning(f"⚠️ [Physics] Violação: Valor negativo ({np.min(data_np):.2f}) detectado em '{source.name}'.")
            return False

        # 2. Resolve Roadway Topology Context (Lanes, Speed Limits)
        edge = self._resolve_associated_edge(source, active_app_state)
        lanes = int(edge.lanes) if edge and isinstance(getattr(edge, "lanes", None), (int, float)) and edge.lanes > 0 else int(source.metadata.get("lanes", 4))
        dt_sec = self._resolve_sampling_interval(data_chunk, source)

        # 3. Dynamic Modality-Aware Physical Bounds Check
        is_valid_bound, max_bound_desc = self._check_dynamic_bounds(
            data_np=data_np,
            sem_type=sem_type,
            unit=unit,
            lanes=lanes,
            edge=edge,
            dt_sec=dt_sec,
            source=source
        )
        if not is_valid_bound:
            logger.warning(
                f"⚠️ [Physics] Violação: Limite físico dinâmico excedido em '{source.name}'. "
                f"Máximo registrado: {np.max(data_np):.2f} > Teto: {max_bound_desc} (Faixas={lanes}, dt={dt_sec:.2f}s, Unidade={unit})."
            )
            return False

        # 4. Kinematic Acceleration Check (for speed time-series)
        if "speed" in sem_lower and len(data_np) > 1 and dt_sec > 0:
            if not self._check_kinematic_acceleration(data_np, unit, dt_sec, source):
                return False

        # 5. Context-Aware Flatline / Dead Sensor Check
        if not self._check_sensor_liveness(data_np, sem_lower, source):
            return False

        # 6. Physics Residual Check (Decoupled from NLP/ModernBERT text reconstruction)
        if agent is not None:
            infer_fn = getattr(agent, "inference", None)
            comp_res_fn = getattr(agent, "compute_physics_residual", None)
            if callable(infer_fn):
                try:
                    analysis = infer_fn({"text": str(source.name), "semantic_type": sem_type})
                    phys_res = analysis.get("physics_residual", 0.0)
                    if isinstance(phys_res, (int, float)) and phys_res > self.max_physics_residual:
                        logger.warning(
                            f"⚠️ [Physics] Violação: Resíduo físico ({phys_res:.4f} > {self.max_physics_residual}) em '{source.name}'."
                        )
                        return False
                except Exception as e:
                    logger.debug(f"[Physics] Verificação de resíduo PINN ignorada: {e}")
            elif callable(comp_res_fn):
                try:
                    res = float(comp_res_fn(data_np, sem_type=sem_type))
                    if res > self.max_physics_residual:
                        logger.warning(
                            f"⚠️ [Physics] Violação: Resíduo físico numérico ({res:.4f} > {self.max_physics_residual}) em '{source.name}'."
                        )
                        return False
                except Exception as e:
                    logger.debug(f"[Physics] Falha na avaliação do resíduo: {e}")

        return True

    def _resolve_associated_edge(self, source: DataSource, app_state: Optional[Any]) -> Optional[MapEdge]:
        """Resolves the MapEdge entity linked to the data source if available in the network topology."""
        if app_state is None:
            return None
        try:
            element_id = None
            get_elem_fn = getattr(app_state, "get_element_for_source", None)
            if callable(get_elem_fn):
                raw_elem = get_elem_fn(source.id)
                if isinstance(raw_elem, str) and raw_elem:
                    element_id = raw_elem
            if not element_id:
                raw_meta = source.metadata.get("edge_id") or source.metadata.get("element_id")
                if isinstance(raw_meta, str) and raw_meta:
                    element_id = raw_meta
            get_edge_fn = getattr(app_state, "get_edge", None)
            if element_id and callable(get_edge_fn):
                edge = get_edge_fn(element_id)
                if edge and isinstance(getattr(edge, "lanes", None), (int, float)):
                    return edge
        except Exception as e:
            logger.debug(f"[Physics] Falha ao resolver MapEdge para '{source.id}': {e}")
        return None

    def _resolve_sampling_interval(self, data_chunk: Optional[List[Any]], source: DataSource) -> float:
        """Determines the effective sampling interval dt in seconds."""
        if data_chunk and len(data_chunk) >= 2:
            timestamps = []
            for item in data_chunk:
                if isinstance(item, dict):
                    ts = item.get("timestamp") or item.get("time") or item.get("ts") or item.get("event_timestamp")
                    if isinstance(ts, (int, float)) and ts > 0:
                        timestamps.append(float(ts))
            if len(timestamps) >= 2:
                deltas = np.diff(timestamps)
                pos_deltas = deltas[deltas > 0]
                if len(pos_deltas) > 0:
                    return float(np.median(pos_deltas))

        dt_meta = source.metadata.get("sampling_interval_sec") or source.metadata.get("dt") or source.metadata.get("interval")
        if isinstance(dt_meta, (int, float)) and dt_meta > 0:
            return float(dt_meta)
        return 1.0

    def _check_dynamic_bounds(
        self,
        data_np: np.ndarray,
        sem_type: str,
        unit: str,
        lanes: int,
        edge: Optional[MapEdge],
        dt_sec: float,
        source: DataSource
    ) -> Tuple[bool, str]:
        """Calculates dynamic physical limits based on roadway capacity and modality."""
        return TrafficSymbolicRules.check_dynamic_bounds(
            data_np=data_np,
            sem_type=sem_type,
            unit=unit,
            lanes=lanes,
            edge=edge,
            dt_sec=dt_sec,
            source=source,
            max_physical_bound=self.max_physical_bound
        )

    def _check_kinematic_acceleration(
        self,
        data_np: np.ndarray,
        unit: str,
        dt_sec: float,
        source: DataSource
    ) -> bool:
        """Verifies if acceleration/deceleration between consecutive points is physically plausible."""
        return TrafficSymbolicRules.check_kinematic_acceleration(
            data_np=data_np,
            unit=unit,
            dt_sec=dt_sec,
            source_name=source.name
        )

    def _check_sensor_liveness(
        self,
        data_np: np.ndarray,
        sem_lower: str,
        source: DataSource
    ) -> bool:
        """Verifies if sensor is truly active."""
        return TrafficSymbolicRules.check_sensor_liveness(
            data_np=data_np,
            sem_lower=sem_lower,
            source_name=source.name
        )
