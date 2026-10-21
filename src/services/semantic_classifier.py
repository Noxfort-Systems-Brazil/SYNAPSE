# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Any, List, Tuple, Optional
import numpy as np
from src.interfaces.quarantine import ISemanticClassifier
from src.domain.entities import DataSource


class SemanticClassifier(ISemanticClassifier):
    """
    Classifies traffic sensor semantics (semantic type, engineering unit, and confidence)
    based on metadata context, payload schema structure, and signal characteristics,
    independent of rigid numerical magnitude assumptions.
    """

    CAMERA_KEYWORDS = ["camera", "cam", "video", "cftv", "vis", "yolo", "det", "vision", "loop", "laço", "inductive"]
    SPEED_KEYWORDS = ["speed", "vel", "radar", "tomtom", "gps", "kmh", "mph", "currentspeed"]
    FLOW_KEYWORDS = ["flow", "fluxo", "volume", "count", "veic", "waze", "currentflow"]
    DENSITY_KEYWORDS = ["density", "densidade", "occ", "occupancy", "rho"]

    def classify(
        self,
        source: DataSource,
        data_np: np.ndarray,
        data_chunk: Optional[List[Any]] = None
    ) -> Tuple[str, str, float]:
        """
        Infers semantic type, engineering unit, and confidence from sensor metadata and schema.
        
        Args:
            source: The DataSource entity.
            data_np: 1D NumPy array of numerical values.
            data_chunk: Optional raw payload chunk for structural schema inspection.
            
        Returns:
            Tuple[str, str, float]: (semantic_type, unit, confidence)
        """
        name_and_conn = f"{source.name} {source.id} {getattr(source, 'connection_string', '') or ''}".lower()

        # 1. Inspect Payload Structure if available
        if data_chunk and len(data_chunk) > 0:
            sample_item = data_chunk[0]
            # Handle list/tuple wrappers like [['2026-10-18,...']] or [{'event_type': ...}]
            if isinstance(sample_item, (list, tuple)) and len(sample_item) > 0:
                inner_item = sample_item[0]
                if isinstance(inner_item, dict):
                    if any(k in inner_item for k in ["event_type", "detections", "vehicles", "objects", "boxes", "tracks"]):
                        return "Vehicle Count", "vehicles", 0.95
                elif isinstance(inner_item, str) and "," in inner_item:
                    parts = [p.strip() for p in inner_item.split(",")]
                    if len(parts) >= 8:
                        return "Vehicle Count", "vehicles", 0.95
            elif isinstance(sample_item, str) and "," in sample_item:
                parts = [p.strip() for p in sample_item.split(",")]
                if len(parts) >= 8:
                    return "Vehicle Count", "vehicles", 0.95

            if isinstance(sample_item, dict):
                # Computer Vision detections / objects
                if any(k in sample_item for k in ["detections", "vehicles", "objects", "boxes", "tracks"]):
                    return "Vehicle Count", "vehicles", 0.95
                # TomTom flowSegmentData with currentSpeed
                if "flowSegmentData" in sample_item:
                    nested = sample_item["flowSegmentData"]
                    if isinstance(nested, dict) and "currentSpeed" in nested:
                        return "Vehicle Speed", "km/h", 0.95
                # Direct keys
                if any(k in sample_item for k in ["currentSpeed", "speed", "velocidade"]):
                    return "Vehicle Speed", "km/h", 0.95
                if any(k in sample_item for k in ["currentFlow", "flow", "fluxo", "volume"]):
                    return "Traffic Flow", "veh/h", 0.95
                if any(k in sample_item for k in ["occupancy", "density", "densidade"]):
                    return "Traffic Density", "veh/km", 0.95
                if any(k in sample_item for k in ["vehicle_count", "counted_in_frame", "count"]):
                    return "Vehicle Count", "vehicles", 0.95

        # 2. Keyword analysis on sensor metadata
        if any(k in name_and_conn for k in self.CAMERA_KEYWORDS):
            return "Vehicle Count", "vehicles", 0.95
        if any(k in name_and_conn for k in self.SPEED_KEYWORDS):
            return "Vehicle Speed", "km/h", 0.95
        if any(k in name_and_conn for k in self.FLOW_KEYWORDS):
            return "Traffic Flow", "veh/h", 0.95
        if any(k in name_and_conn for k in self.DENSITY_KEYWORDS):
            return "Traffic Density", "veh/km", 0.95

        # 3. Fallback Statistical Inference (when schema & metadata are unlabelled)
        if len(data_np) == 0:
            return "Traffic State", "units", 0.30

        # Discreteness check: Vehicle count is inherently non-negative integer valued
        is_discrete = bool(np.all(np.equal(np.mod(data_np, 1), 0)) and np.all(data_np >= 0))
        mean_val = float(np.mean(data_np))
        max_val = float(np.max(data_np))

        if is_discrete and max_val <= 100.0:
            return "Vehicle Count", "vehicles", 0.65

        # Beyond physical road vehicle speed ceiling (~180-200 km/h) => Traffic Flow (veh/h)
        if mean_val > 180.0:
            return "Traffic Flow", "veh/h", 0.70
        elif 5.0 <= mean_val <= 180.0:
            return "Vehicle Speed", "km/h", 0.65
        else:
            return "Traffic State", "units", 0.40

