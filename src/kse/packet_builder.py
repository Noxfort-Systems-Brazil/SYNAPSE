# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import time
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.utils.debug_logger import carina_logger, carina_input_logger, carina_output_logger
from src.physics.constants import (
    DEFAULT_JAM_DENSITY_PER_LANE,
    DEFAULT_VEHICLE_EFFECTIVE_LEN_M,
    occupancy_from_density,
)
from src.physics.traffic_hydrodynamics import TrafficHydrodynamicEngine
from src.physics.queue_dynamics import TrafficQueueCalculator
from src.kse.kinematic_extrapolator import KinematicExtrapolator


class PacketBuilder:
    """
    Single Responsibility: Build and validate HFT transmission packets (SOLID: SRP & DIP).
    
    Handles:
    - Converting raw edge state dicts into the strict HFT schema.
    - Validating that packets contain real data (transmission gate).
    - Debug logging of packet construction (text log + JSONL input/output dumps).
    
    Delegates:
    - Continuum traffic physics & graph interpolation to TrafficHydrodynamicEngine.
    - Physical capacity & queuing to TrafficQueueCalculator.
    - Dead reckoning projection to KinematicExtrapolator.
    """

    @staticmethod
    def build(data: Dict[str, Any], source: str, app_state: Optional[Any] = None) -> Optional[dict]:
        """
        Formats raw edge/node data into a strict HFT packet covering all network edges (streets).
        
        Args:
            data: Dict mapping edge_id or node_id -> {density, speed, queue, ...}
            source: Origin label ("realtime", "historical", "kse_dead_reckoning")
            app_state: Optional AppState reference to map all SUMO edges/streets
            
        Returns:
            Formatted packet dict, or None if data is empty (gate).
        """
        # --- GATE #1: Empty data dict ---
        if not data:
            return None

        _build_start = time.time()
        _ts_start = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        _iso_start = datetime.now().isoformat()

        # Log Raw Input to JSONL dump (strip 32-dim latent embeddings to avoid redundant bloat)
        try:
            slim_input = {
                k: ({ik: iv for ik, iv in v.items() if ik != "embedding"} if isinstance(v, dict) and "embedding" in v else v)
                for k, v in data.items()
            }
            carina_input_logger.log({
                "timestamp": _build_start,
                "iso_time": _iso_start,
                "source": source,
                "total_inputs": len(data),
                "data": slim_input,
            })
        except Exception:
            pass

        traffic_list: List[Dict[str, Any]] = []
        k_jam = DEFAULT_JAM_DENSITY_PER_LANE
        veh_effective_len = DEFAULT_VEHICLE_EFFECTIVE_LEN_M

        all_edges = []
        get_node_fn = None
        if app_state is not None:
            get_all_edges_fn = getattr(app_state, "get_all_edges", None)
            if callable(get_all_edges_fn):
                all_edges = get_all_edges_fn() or []
            else:
                topo = getattr(app_state, "topology", None)
                topo_edges_fn = getattr(topo, "get_all_edges", None)
                if callable(topo_edges_fn):
                    all_edges = topo_edges_fn() or []

            cand_node_fn = getattr(app_state, "get_node", None)
            if callable(cand_node_fn):
                get_node_fn = cand_node_fn
            else:
                topo = getattr(app_state, "topology", None)
                topo_node_fn = getattr(topo, "get_node", None)
                if callable(topo_node_fn):
                    get_node_fn = topo_node_fn

        if all_edges:
            tls_cache: Dict[str, bool] = {}
            for edge in all_edges:
                edge_id = str(edge.id)
                edge_len = getattr(edge, "length", 100.0)
                edge_lanes = getattr(edge, "lanes", 1)
                signal_group = getattr(edge, "signal_group_id", -1)
                is_controlled = (signal_group != -1)
                if not is_controlled and get_node_fn is not None:
                    to_node_id = getattr(edge, "to_node", None)
                    if to_node_id:
                        cached_tls = tls_cache.get(to_node_id)
                        if cached_tls is None:
                            node = get_node_fn(to_node_id)
                            cached_tls = False
                            if node is not None:
                                tl_id = getattr(node, "tl_logic_id", None)
                                node_type = str(getattr(node, "node_type", "")).lower()
                                cached_tls = bool(tl_id or node_type.startswith("traffic_light"))
                            tls_cache[to_node_id] = cached_tls
                        is_controlled = cached_tls

                v_free = getattr(edge, "max_speed", 13.89)
                max_capacity = TrafficQueueCalculator.calculate_storage_capacity(
                    edge_len, edge_lanes, veh_effective_len
                )
                density, speed = TrafficHydrodynamicEngine.resolve_edge_state(edge, data, k_jam)
                occupancy = occupancy_from_density(density, k_jam)
                queue = TrafficQueueCalculator.estimate_edge_queue(
                    density=density,
                    speed=speed,
                    v_free=v_free,
                    max_capacity=max_capacity,
                    signal_group_id=signal_group,
                    is_controlled=is_controlled,
                    k_jam=k_jam,
                )

                traffic_list.append({
                    "edge_id": edge_id,
                    "density": float(density),
                    "speed": float(speed),
                    "queue": int(queue),
                    "occupancy": float(occupancy),
                })
        else:
            # Fallback path: iterate raw data items
            for source_id, metrics in data.items():
                density, speed = TrafficHydrodynamicEngine.resolve_unmapped_source(metrics, k_jam)
                occ = occupancy_from_density(density, k_jam)
                queue = TrafficQueueCalculator.estimate_fallback_queue(density, speed, k_jam)

                traffic_list.append({
                    "edge_id": str(source_id),
                    "density": density,
                    "speed": speed,
                    "queue": queue,
                    "occupancy": occ,
                })

        # --- GATE #2: No edges after processing ---
        if not traffic_list:
            return None

        packet = {
            "timestamp": time.time(),
            "source": source,
            "traffic": traffic_list,
        }

        # --- Debug Log ---
        _build_end = time.time()
        _ts_end = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        _build_time_ms = (_build_end - _build_start) * 1000.0

        try:
            carina_output_logger.log({
                "timestamp": packet["timestamp"],
                "iso_time": datetime.now().isoformat(),
                "source": source,
                "total_edges": len(traffic_list),
                "build_time_ms": round(_build_time_ms, 2),
                "traffic": traffic_list,
            })
        except Exception:
            pass

        carina_logger.info(
            f"KSE_BUILD | mode={source} | edges={len(traffic_list)} "
            f"| start={_ts_start} | end={_ts_end} "
            f"| build_time={_build_time_ms:.2f}ms"
        )

        return packet

    @staticmethod
    def extrapolate(base_state: Dict[str, Any], dt: float) -> Dict[str, Any]:
        """
        Projects traffic metrics forward using KSE physics velocities.
        Preserves backward compatibility by delegating to KinematicExtrapolator.
        """
        return KinematicExtrapolator.extrapolate(base_state, dt)
