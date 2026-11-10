# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import logging
import numpy as np
from typing import Dict, Any, Tuple, Optional

from src.kse.packet_builder import PacketBuilder
from src.physics.constants import SpeedConverter

logger = logging.getLogger("Synapse.TelemetryAggregator")

# --- Telemetry Invariants & Baseline Constants ---
DEFAULT_TELEMETRY_LOSS: float = 0.008
DEFAULT_TELEMETRY_DRIFT: float = 0.012
DEFAULT_TELEMETRY_FACTOR: float = 1200.0
DEFAULT_TELEMETRY_QUALITY_TAU: float = 0.08
MAX_TELEMETRY_LOSS_CEILING: float = 0.5
MIN_TELEMETRY_LOSS_FLOOR: float = 0.0001


def compute_telemetry_quality(loss: float, tau: float = DEFAULT_TELEMETRY_QUALITY_TAU) -> int:
    """Calculates sensor quality score [10, 100] via exponential decay Q(L) = 100 * exp(-L / tau)."""
    score = 100.0 * np.exp(-max(0.0, float(loss)) / tau)
    return int(max(10, min(100, round(score))))


class InferenceTelemetryAggregator:
    """Aggregates edge fluid metrics and sensor MLOps telemetry."""

    @staticmethod
    def build_fluid_edge_metrics(snapshot: Any, app_state: Any) -> Tuple[Dict[str, Any], float, float]:
        """Builds fluid dynamics telemetry across the road network (LWR / Greenshields)."""
        edge_data = {}
        mean_speed = 0.0
        mean_occupancy = 0.0
        try:
            packet = PacketBuilder.build(snapshot, "realtime", app_state)
            if packet and "traffic" in packet:
                speeds = []
                occs = []
                for item in packet["traffic"]:
                    raw_s = float(item["speed"])
                    speed_kmh = float(SpeedConverter.to_kmh(raw_s, "m/s"))
                    edge_id = str(item["edge_id"])
                    density_val = float(item["density"])
                    occ_val = float(item["occupancy"])
                    queue_val = int(item["queue"])

                    edge_data[edge_id] = {
                        "speed": round(speed_kmh, 1),
                        "density": round(density_val, 1),
                        "occupancy": round(occ_val, 3),
                        "queue": queue_val,
                    }
                    speeds.append(speed_kmh)
                    occs.append(occ_val)

                if speeds:
                    mean_speed = round(sum(speeds) / len(speeds), 1)
                if occs:
                    mean_occupancy = round(sum(occs) / len(occs), 3)
        except Exception as e:
            logger.warning(f"Failed to generate fluid dynamic edge metrics: {e}")

        return edge_data, mean_speed, mean_occupancy

    @classmethod
    def aggregate_mlops_telemetry(
        cls,
        results: Dict[str, Any],
        graph_manager: Any,
        app_state: Any,
        mean_speed: float
    ) -> Tuple[Dict[str, float], Dict[str, float], Dict[str, int], float, float, float]:
        fuser_loss = float(results.get("fuser_loss", DEFAULT_TELEMETRY_LOSS))
        fuser_drift = float(results.get("fuser_drift", DEFAULT_TELEMETRY_DRIFT))

        losses = {}
        drift_scores = {}
        qualities = {}

        # 1. Per-node telemetry from graph
        for node_id, node in graph_manager.nodes.items():
            node_loss = getattr(getattr(node, "state", None), "last_loss", DEFAULT_TELEMETRY_LOSS)
            node_psi = getattr(getattr(node, "state", None), "last_psi", DEFAULT_TELEMETRY_DRIFT)
            losses[node_id] = float(max(MIN_TELEMETRY_LOSS_FLOOR, min(MAX_TELEMETRY_LOSS_CEILING, node_loss)))
            drift_scores[node_id] = float(max(MIN_TELEMETRY_LOSS_FLOOR, min(MAX_TELEMETRY_LOSS_CEILING, node_psi)))
            qualities[node_id] = compute_telemetry_quality(losses[node_id])

        # 2. Map to data sources from AppState
        get_elems_fn = getattr(app_state, "get_elements_for_source", None)
        get_elem_fn = getattr(app_state, "get_element_for_source", None)
        get_edge_fn = getattr(app_state, "get_edge", None)
        get_all_edges_fn = getattr(app_state, "get_all_edges", None)

        for src in (app_state.get_all_data_sources() or []):
            is_local = getattr(src, "is_local", True)
            associated_elements = []
            if is_local:
                if callable(get_elems_fn):
                    associated_elements = get_elems_fn(src.id)
                elif callable(get_elem_fn):
                    single = get_elem_fn(src.id)
                    if single:
                        associated_elements = [single]
                if not associated_elements:
                    assoc_attr = getattr(src, "associated_element", None)
                    if assoc_attr:
                        associated_elements = [assoc_attr]

            src_node_losses = []
            src_node_drifts = []

            for elem_id in associated_elements:
                if elem_id in losses:
                    src_node_losses.append(losses[elem_id])
                    src_node_drifts.append(drift_scores[elem_id])
                else:
                    target_edge = get_edge_fn(elem_id) if callable(get_edge_fn) else None
                    if not target_edge and callable(get_all_edges_fn):
                        clean_id = elem_id.lstrip("-")
                        for e in (get_all_edges_fn() or []):
                            if e.id == elem_id or e.id.lstrip("-") == clean_id:
                                target_edge = e
                                break
                    if target_edge:
                        edge_nodes = [n for n in (target_edge.from_node, target_edge.to_node) if n in losses]
                        for n in edge_nodes:
                            src_node_losses.append(losses[n])
                            src_node_drifts.append(drift_scores[n])

            if src_node_losses:
                losses[src.id] = float(np.mean(src_node_losses))
                drift_scores[src.id] = float(np.mean(src_node_drifts))
                qualities[src.id] = compute_telemetry_quality(losses[src.id])
                continue

            # Unmapped / Global Data Source
            sem_type = (getattr(src, "semantic_type", "") or "").lower()
            val = getattr(src, "latest_value", None)

            if "speed" in sem_type or "velocidade" in sem_type:
                if val is not None and isinstance(val, (int, float)) and val > 0:
                    val_kmh = float(val * 3.6) if val < 45.0 else float(val)
                    comp_speed = mean_speed if mean_speed > 0 else 10.0
                    speed_rel_diff = abs(val_kmh - comp_speed) / max(comp_speed, 10.0)
                    global_loss = float(max(0.002, min(0.3, 0.005 + speed_rel_diff * 0.05)))
                else:
                    global_loss = fuser_loss

                losses[src.id] = global_loss
                drift_scores[src.id] = fuser_drift
                qualities[src.id] = compute_telemetry_quality(global_loss)
            elif "flow" in sem_type or "fluxo" in sem_type or "count" in sem_type:
                flow_scale = 1.0
                if val is not None and isinstance(val, (int, float)) and val > 0:
                    flow_scale = min(2.0, max(0.5, float(val)))
                global_loss = float(max(0.002, min(0.3, fuser_loss * (0.9 + 0.2 * (flow_scale % 1.0)))))
                losses[src.id] = global_loss
                drift_scores[src.id] = fuser_drift
                qualities[src.id] = compute_telemetry_quality(global_loss)
            else:
                base_loss = fuser_loss if fuser_loss > 0 else DEFAULT_TELEMETRY_LOSS
                losses[src.id] = base_loss
                drift_scores[src.id] = fuser_drift
                qualities[src.id] = compute_telemetry_quality(losses[src.id])

        avg_loss = float(sum(losses.values()) / len(losses)) if losses else float(results.get("security_score", DEFAULT_TELEMETRY_LOSS))
        avg_drift = float(sum(drift_scores.values()) / len(drift_scores)) if drift_scores else DEFAULT_TELEMETRY_DRIFT

        if fuser_loss <= 0.0:
            fuser_loss = avg_loss
        if fuser_drift <= 0.0:
            fuser_drift = avg_drift

        return losses, drift_scores, qualities, fuser_loss, fuser_drift, avg_loss
