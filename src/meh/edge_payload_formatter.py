# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Dict, Any, Optional
from src.physics.queue_dynamics import TrafficQueueCalculator
from src.physics.constants import (
    DEFAULT_JAM_DENSITY_PER_LANE,
    DEFAULT_VEHICLE_EFFECTIVE_LEN_M,
)

VEH_EFFECTIVE_LEN = DEFAULT_VEHICLE_EFFECTIVE_LEN_M
K_JAM = DEFAULT_JAM_DENSITY_PER_LANE


class EdgePayloadFormatter:
    """
    Translates and normalizes flat sensor metrics into structured per-edge KSE payload dictionaries.
    """

    @staticmethod
    def format_edge_payload(
        flat_data: Dict[str, float],
        app_state: Optional[Any] = None,
        sensor_profiles: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Dict[str, float]]:
        result: Dict[str, Dict[str, float]] = {}
        if not flat_data:
            return result

        edges = []
        if app_state is not None:
            get_all_edges_fn = getattr(app_state, "get_all_edges", None)
            if callable(get_all_edges_fn):
                try:
                    edges = get_all_edges_fn() or []
                except Exception:
                    edges = []
            else:
                network = getattr(app_state, "network", None)
                net_edges = getattr(network, "edges", None)
                if isinstance(net_edges, dict):
                    edges = list(net_edges.values())

        if edges:
            for edge in edges:
                v_free = getattr(edge, "max_speed", 13.89)
                edge_len = getattr(edge, "length", 100.0)
                edge_lanes = getattr(edge, "lanes", 1)
                max_capacity = max(1, int((edge_len / VEH_EFFECTIVE_LEN) * edge_lanes))

                density_val = 4.0
                speed_val = v_free
                queue_val = 0.0

                speed_key = f"{edge.id}_speed"
                density_key = f"{edge.id}_density"
                queue_key = f"{edge.id}_queue"

                # Check explicit edge keys
                if speed_key in flat_data:
                    speed_val = float(flat_data[speed_key])
                if density_key in flat_data:
                    density_val = float(flat_data[density_key])
                if queue_key in flat_data:
                    queue_val = float(flat_data[queue_key])

                # Check associated sensors in AppState
                associated_sources = []
                get_assoc_fn = getattr(app_state, "get_sources_associated_with_element", None) if app_state is not None else None
                if callable(get_assoc_fn):
                    try:
                        associated_sources = get_assoc_fn(edge.id) or []
                    except Exception:
                        associated_sources = []

                matched_sensor = False
                for s_id in associated_sources:
                    if f"{s_id}_speed" in flat_data:
                        speed_val = float(flat_data[f"{s_id}_speed"])
                        density_val = max(0.5, min(K_JAM, K_JAM * (1.0 - min(1.0, speed_val / max(1.0, v_free)))))
                        matched_sensor = True
                        break
                    elif s_id in flat_data:
                        s_reading = float(flat_data[s_id])
                        if s_reading > 3.0:
                            speed_val = max(1.0, min(v_free * 1.1, s_reading))
                            density_val = max(0.5, min(K_JAM, K_JAM * (1.0 - min(1.0, speed_val / max(1.0, v_free)))))
                        else:
                            density_val = max(0.5, min(K_JAM, s_reading * 10.0))
                            speed_val = max(1.0, v_free * (1.0 - (density_val / K_JAM)))
                        matched_sensor = True
                        break

                # If unmapped by local sensors, apply macroscopic global data (TomTom / Waze)
                if not matched_sensor:
                    if "speed" in flat_data:
                        raw_macro_s = float(flat_data["speed"])
                        speed_val = max(1.0, min(v_free * 1.1, raw_macro_s))
                        density_val = max(0.5, min(K_JAM, K_JAM * (1.0 - min(1.0, speed_val / max(1.0, v_free)))))
                    elif "density" in flat_data:
                        density_val = max(0.5, min(K_JAM, float(flat_data["density"])))
                        speed_val = max(1.0, v_free * (1.0 - (density_val / K_JAM)))
                    else:
                        get_sources_fn = getattr(app_state, "get_all_data_sources", None) if app_state is not None else None
                        get_elems_fn = getattr(app_state, "get_elements_for_source", None) if app_state is not None else None
                        if callable(get_sources_fn):
                            for src in (get_sources_fn() or []):
                                if not getattr(src, "is_local", True):
                                    src_meta = getattr(src, "metadata", {}) or {}
                                    if isinstance(src_meta, dict):
                                        ext_mode = src_meta.get("extraction_mode", "")
                                        ext_path = src_meta.get("extraction_path", [])
                                        if ext_mode == "detection_list" or (isinstance(ext_path, list) and "jams" in ext_path):
                                            continue
                                    if callable(get_elems_fn):
                                        bound_elems = get_elems_fn(src.id)
                                        if bound_elems:
                                            continue
                                    raw_latest = getattr(src, "latest_value", None)
                                    if isinstance(raw_latest, (int, float)) and not isinstance(raw_latest, bool):
                                        g_val = float(raw_latest)
                                        if g_val > 0.0:
                                            speed_val = max(1.0, min(v_free * 1.1, g_val))
                                            density_val = max(0.5, min(K_JAM, K_JAM * (1.0 - min(1.0, speed_val / max(1.0, v_free)))))
                                            break

                if queue_val <= 0.0:
                    signal_group = getattr(edge, "signal_group_id", -1)
                    is_controlled = (signal_group != -1)
                    if not is_controlled and app_state is not None:
                        to_node_id = getattr(edge, "to_node", None)
                        if to_node_id:
                            node = None
                            get_node_fn = getattr(app_state, "get_node", None)
                            if callable(get_node_fn):
                                node = get_node_fn(to_node_id)
                            else:
                                topo = getattr(app_state, "topology", None)
                                topo_get_node = getattr(topo, "get_node", None)
                                if callable(topo_get_node):
                                    node = topo_get_node(to_node_id)
                            if node is not None:
                                tl_id = getattr(node, "tl_logic_id", None)
                                node_type = str(getattr(node, "node_type", "")).lower()
                                if tl_id or node_type.startswith("traffic_light"):
                                    is_controlled = True

                    queue_val = float(TrafficQueueCalculator.estimate_edge_queue(
                        density=density_val,
                        speed=speed_val,
                        v_free=v_free,
                        max_capacity=max_capacity,
                        signal_group_id=signal_group,
                        is_controlled=is_controlled,
                        k_jam=K_JAM,
                    ))

                occupancy_val = min(0.98, max(0.01, density_val / K_JAM))
                speed_val = max(1.0, min(v_free * 1.1, speed_val))
                density_val = min(K_JAM, max(0.5, density_val))

                result[edge.id] = {
                    "speed": speed_val,
                    "density": density_val,
                    "queue": int(round(min(max_capacity, max(0, queue_val)))),
                    "occupancy": occupancy_val,
                }
        else:
            profiles = sensor_profiles or {}
            for sensor_id in profiles.keys():
                d_val = float(flat_data.get(f"{sensor_id}_density", flat_data.get("density", 15.0)))
                s_val = float(flat_data.get(f"{sensor_id}_speed", flat_data.get("speed", 13.89)))
                q_val = float(flat_data.get(f"{sensor_id}_queue", flat_data.get("queue", 0.0)))
                if q_val <= 0.0:
                    q_val = float(TrafficQueueCalculator.estimate_fallback_queue(
                        density=d_val,
                        speed=s_val,
                        k_jam=K_JAM,
                    ))
                result[sensor_id] = {
                    "speed": s_val,
                    "density": d_val,
                    "queue": int(round(q_val)),
                    "occupancy": min(0.98, max(0.02, d_val / K_JAM)),
                }

            if not result and flat_data:
                d_val = float(flat_data.get("density", 15.0))
                result["synthetic_edge"] = {
                    "speed": float(flat_data.get("speed", 40.0)),
                    "density": d_val,
                    "queue": int(round(float(flat_data.get("queue", 1.0)))),
                    "occupancy": min(1.0, max(0.05, d_val / 100.0)),
                }

        return result
