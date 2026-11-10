# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import math
from typing import Tuple, List, Optional, Dict, Any

from src.domain.entities import MapEdge, DataSource



def compute_edge_vector(edge: MapEdge) -> Tuple[float, float]:
    """Calculates normalized (dx, dy) directional vector from edge geometry."""
    if not edge.shape or len(edge.shape) < 2:
        return (1.0, 0.0)
    p_start = edge.shape[0]
    p_end = edge.shape[-1]
    dx = p_end[0] - p_start[0]
    dy = p_end[1] - p_start[1]
    norm = math.hypot(dx, dy)
    if norm < 1e-6:
        return (1.0, 0.0)
    return (dx / norm, dy / norm)


def extract_fluid_vector(
    source: DataSource,
    data_chunk: Optional[List[Any]]
) -> Optional[Tuple[float, float]]:
    """
    Extracts canonical directional vector (dx, dy) from fluid kinematics,
    SVision payloads, optical tracking, or geodetic polyline drift.
    """
    # 1. Inspect direct telemetry chunk sample
    if data_chunk and len(data_chunk) > 0:
        sample = data_chunk[0]
        if isinstance(sample, dict):
            # 1.1 Direct angle / heading / bearing keys
            for deg_k in ("direction_deg", "flow_vector_deg", "bearing", "heading", "azimuth", "angle"):
                if deg_k in sample:
                    try:
                        deg = float(sample[deg_k])
                        rad = math.radians(deg)
                        return (math.cos(rad), math.sin(rad))
                    except (ValueError, TypeError):
                        pass

            # 1.2 Direct 2D vector [dx, dy]
            vec_raw = sample.get("vector") or sample.get("motion_vector") or sample.get("flow_vector")
            if isinstance(vec_raw, (list, tuple)) and len(vec_raw) >= 2:
                try:
                    vx, vy = float(vec_raw[0]), float(vec_raw[1])
                    norm = math.hypot(vx, vy)
                    if norm > 1e-6:
                        return (vx / norm, vy / norm)
                except (ValueError, TypeError):
                    pass

            # 1.3 Detections / trackings average vector (Format A - YOLO / ByteTrack)
            dets = sample.get("detections") or sample.get("tracks")
            if isinstance(dets, list) and dets:
                sum_dx, sum_dy, count = 0.0, 0.0, 0
                for d in dets:
                    if isinstance(d, dict):
                        d_vec = d.get("vector") or d.get("motion_vector")
                        if isinstance(d_vec, (list, tuple)) and len(d_vec) >= 2:
                            try:
                                sum_dx += float(d_vec[0])
                                sum_dy += float(d_vec[1])
                                count += 1
                            except (ValueError, TypeError):
                                pass
                        elif "direction_angle" in d or "bearing_deg" in d or "angle" in d:
                            try:
                                ang = float(d.get("direction_angle") or d.get("bearing_deg") or d.get("angle"))
                                rad = math.radians(ang)
                                sum_dx += math.cos(rad)
                                sum_dy += math.sin(rad)
                                count += 1
                            except (ValueError, TypeError):
                                pass
                if count > 0:
                    norm = math.hypot(sum_dx, sum_dy)
                    if norm > 1e-6:
                        return (sum_dx / norm, sum_dy / norm)

    # 2. Inspect DataSource metadata
    meta = source.metadata or {}
    for deg_k in ("direction_deg", "flow_vector_deg", "bearing", "heading", "azimuth", "angle"):
        if deg_k in meta:
            try:
                deg = float(meta[deg_k])
                rad = math.radians(deg)
                return (math.cos(rad), math.sin(rad))
            except (ValueError, TypeError):
                pass

    # 3. Inspect projected SUMO polyline in metadata
    sumo_poly = meta.get("sumo_polyline")
    if isinstance(sumo_poly, list) and len(sumo_poly) >= 2:
        try:
            p_start = sumo_poly[0]
            p_end = sumo_poly[-1]
            dx = float(p_end[0] - p_start[0])
            dy = float(p_end[1] - p_start[1])
            norm = math.hypot(dx, dy)
            if norm > 1e-4:
                return (dx / norm, dy / norm)
        except (ValueError, TypeError, IndexError):
            pass

    return None


def align_fluid_vector(
    fluid_vec: Tuple[float, float],
    candidate_edges: List[MapEdge]
) -> Optional[Dict[str, Any]]:
    """
    Calculates deterministic physical alignment between extracted fluid vector
    and candidate edge vectors using cosine similarity dot products.
    """
    if len(candidate_edges) < 2:
        return None

    edge_a = candidate_edges[0]
    edge_b = candidate_edges[1]
    vec_a = compute_edge_vector(edge_a)
    vec_b = compute_edge_vector(edge_b)

    dot_a = fluid_vec[0] * vec_a[0] + fluid_vec[1] * vec_a[1]
    dot_b = fluid_vec[0] * vec_b[0] + fluid_vec[1] * vec_b[1]

    # Margin check: vectors must exhibit distinct directional separation
    margin = abs(dot_a - dot_b)
    if margin < 0.40:
        return None

    if dot_a > dot_b:
        chosen_edge = edge_a
        chosen_vec = vec_a
        orientation = "IDA"
        confidence = float(min(0.99, max(0.85, (dot_a + 1.0) / 2.0)))
    else:
        chosen_edge = edge_b
        chosen_vec = vec_b
        orientation = "VOLTA"
        confidence = float(min(0.99, max(0.85, (dot_b + 1.0) / 2.0)))

    prob_a = float(max(0.01, min(0.99, (dot_a + 1.0) / 2.0)))
    prob_b = float(max(0.01, min(0.99, (dot_b + 1.0) / 2.0)))
    total = prob_a + prob_b
    if total > 0:
        prob_a /= total
        prob_b /= total

    return {
        "orientation": orientation,
        "primary_edge_id": chosen_edge.id,
        "secondary_edge_id": None,
        "channels": {},
        "confidence": confidence,
        "vector": chosen_vec,
        "method": "fluid_vector_alignment",
        "probabilities": {"IDA": prob_a, "VOLTA": prob_b},
        "margin": float(abs(prob_a - prob_b))
    }


def detect_multichannel(
    source: DataSource,
    candidate_edges: List[MapEdge],
    data_chunk: Optional[List[Any]]
) -> Optional[Dict[str, Any]]:
    """Identifies whether incoming sensor payload has separate channels for opposing directions."""
    if len(candidate_edges) < 2:
        return None

    # 1. Inspect metadata for channel definitions
    meta = source.metadata or {}
    channels_meta = meta.get("channels") or meta.get("lanes")
    if isinstance(channels_meta, dict) and len(channels_meta) >= 2:
        keys = list(channels_meta.keys())
        return {
            "orientation": "DUPLO",
            "primary_edge_id": candidate_edges[0].id,
            "secondary_edge_id": candidate_edges[1].id,
            "channels": {
                keys[0]: candidate_edges[0].id,
                keys[1]: candidate_edges[1].id
            },
            "confidence": 0.95,
            "vector": compute_edge_vector(candidate_edges[0]),
            "method": "multichannel_metadata_split"
        }

    # 2. Inspect data_chunk items for dual direction keys or channel lists
    if data_chunk and len(data_chunk) > 0:
        sample = data_chunk[0]
        if isinstance(sample, dict):
            # 2.1 Direct dual keys in dict
            has_inbound = any(k in sample for k in ("inbound", "ida", "north", "northbound", "lane_1", "lane_in"))
            has_outbound = any(k in sample for k in ("outbound", "volta", "south", "southbound", "lane_2", "lane_out"))
            if has_inbound and has_outbound:
                return {
                    "orientation": "DUPLO",
                    "primary_edge_id": candidate_edges[0].id,
                    "secondary_edge_id": candidate_edges[1].id,
                    "channels": {
                        "inbound": candidate_edges[0].id,
                        "outbound": candidate_edges[1].id
                    },
                    "confidence": 0.92,
                    "vector": compute_edge_vector(candidate_edges[0]),
                    "method": "multichannel_payload_split"
                }

            # 2.2 SVision channels or lanes list
            raw_channels = sample.get("channels") or sample.get("lanes")
            if isinstance(raw_channels, list) and len(raw_channels) >= 2:
                # Resolve channel to edge via vector if available, else sequential
                ch0 = raw_channels[0] if isinstance(raw_channels[0], dict) else {}
                ch1 = raw_channels[1] if isinstance(raw_channels[1], dict) else {}

                ch0_id = ch0.get("channel_id") or ch0.get("id") or ch0.get("lane_id") or "ch_0"
                ch1_id = ch1.get("channel_id") or ch1.get("id") or ch1.get("lane_id") or "ch_1"

                # Check if channel 0 aligns better with edge 0 or edge 1
                deg0 = ch0.get("direction_deg") or ch0.get("flow_vector_deg")
                deg1 = ch1.get("direction_deg") or ch1.get("flow_vector_deg")

                edge_0_target = candidate_edges[0].id
                edge_1_target = candidate_edges[1].id

                if deg0 is not None:
                    rad0 = math.radians(float(deg0))
                    vec_ch0 = (math.cos(rad0), math.sin(rad0))
                    v0 = compute_edge_vector(candidate_edges[0])
                    v1 = compute_edge_vector(candidate_edges[1])
                    dot0 = vec_ch0[0] * v0[0] + vec_ch0[1] * v0[1]
                    dot1 = vec_ch0[0] * v1[0] + vec_ch0[1] * v1[1]
                    if dot1 > dot0:
                        edge_0_target = candidate_edges[1].id
                        edge_1_target = candidate_edges[0].id

                return {
                    "orientation": "DUPLO",
                    "primary_edge_id": candidate_edges[0].id,
                    "secondary_edge_id": candidate_edges[1].id,
                    "channels": {
                        str(ch0_id): edge_0_target,
                        str(ch1_id): edge_1_target
                    },
                    "confidence": 0.96,
                    "vector": compute_edge_vector(candidate_edges[0]),
                    "method": "svision_multichannel_split"
                }

    return None

