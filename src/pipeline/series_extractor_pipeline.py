# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: src/pipeline/series_extractor_pipeline.py
# Description: Pure Orchestrator for extracting 1D time-series from sensor streams (SOLID: SRP & Clean Arch).

from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
from src.interfaces.quarantine import ISeriesExtractorPipeline
from src.pipeline.series.recipe_compiler import SeriesRecipeCompiler
from src.pipeline.series.payload_parser import SeriesPayloadParser


class SeriesExtractorPipeline(ISeriesExtractorPipeline):
    """
    Intelligent Schema-Aware Pipeline Orchestrator for extracting and sanitizing
    1D numeric time-series from heterogeneous sensor payloads.
    Delegates recipe compilation and payload parsing to specialized SRP components.
    """

    # Priority keys for traffic measurements (in order of priority)
    PRIMARY_TRAFFIC_KEYS: List[str] = [
        "currentspeed_kmh", "freeflowspeed_kmh", "currentSpeed", "freeFlowSpeed",
        "speed", "velocidade", "vel", "kmh", "speedkmh", "estimated_speed_kmh", "speed_kmh",
        "currentFlow", "flow", "fluxo", "volume", "q", "field_7", "field_8",
        "vehicle_count", "counted_in_frame", "count", "contagem", "cars", "veic",
        "occupancy", "density", "densidade", "rho", "occ",
        "reading", "value", "val", "delay", "delay_seconds"
    ]

    # Keys that represent object/detection lists in computer vision / camera payloads
    DETECTION_LIST_KEYS: List[str] = [
        "recognitions", "jams", "detections", "vehicles", "objects", "boxes",
        "tracks", "detected_objects", "targets", "plates", "items"
    ]

    # Explicit blacklist of ID, timestamp, and metadata keys that must never be treated as measurements
    IGNORE_KEYS: Set[str] = {
        "packet_id", "sensor_id", "device_id", "segmentid", "segment_id",
        "track_id", "frame_id", "camera_id", "node_id", "edge_id", "id",
        "timestamp", "starttimemillis", "endtimemillis", "created_at", "updated_at",
        "time", "date", "lat", "lon", "latitude", "longitude", "status", "version"
    }

    def __init__(self, traffic_keys: Optional[List[str]] = None, to_si: bool = False):
        self.traffic_keys = traffic_keys or self.PRIMARY_TRAFFIC_KEYS
        self.to_si = to_si
        self.recipe: Optional[dict] = None

    @staticmethod
    def get_si_conversion_factor(unit: Optional[str], modality: Optional[str] = None) -> Tuple[float, str]:
        """Returns the multiplicative factor to convert raw unit to International System (SI)."""
        return SeriesRecipeCompiler.get_si_conversion_factor(unit, modality)

    def compile_recipe(
        self,
        sample_chunk: List[Any],
        modality: Optional[str] = None,
        unit: Optional[str] = None,
        to_si: bool = True
    ) -> dict:
        """
        Discovers the optimal O(1) extraction recipe from sample packets.
        Compiles the direct access path, parsing mode, and SI conversion factor.
        """
        self.to_si = to_si
        self.recipe = SeriesRecipeCompiler.compile_recipe(
            sample_chunk=sample_chunk,
            traffic_keys=self.traffic_keys,
            detection_list_keys=self.DETECTION_LIST_KEYS,
            ignore_keys=self.IGNORE_KEYS,
            modality=modality,
            unit=unit,
            to_si=to_si,
        )
        return self.recipe

    def extract(self, data_chunk: List[Any]) -> np.ndarray:
        """
        Extracts a clean 1D float32 NumPy array from any arbitrary payload list.
        """
        if not data_chunk:
            return np.array([], dtype=np.float32)

        values = [self._parse_item(item) for item in data_chunk]
        return np.array(values, dtype=np.float32)

    def _parse_item(self, item: Any) -> float:
        """Parses a single item into a float measurement."""
        return SeriesPayloadParser.parse_item(
            item=item,
            recipe=self.recipe,
            traffic_keys=self.traffic_keys,
            detection_list_keys=self.DETECTION_LIST_KEYS,
            ignore_keys=self.IGNORE_KEYS,
            to_si=self.to_si,
        )

    def _extract_value(self, val: Any) -> Optional[float]:
        """Safely extracts a numeric float from scalar or string value."""
        return SeriesPayloadParser.extract_value(val)
