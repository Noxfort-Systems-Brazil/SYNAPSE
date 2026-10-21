# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import time
import logging
from typing import Any, Optional
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from src.domain.app_state import AppState
from src.domain.entities import SourceStatus
from src.managers.graph_manager import GraphManager
from src.pipeline.series_extractor_pipeline import SeriesExtractorPipeline
from src.physics.sensor_unit_converter import SensorUnitConverter


class DataFlowRouter(QObject):
    """
    Handles real-time sensor data ingestion, extraction, and graph memory dispatch (Fast Path).

    SOLID Roles:
    - [SRP] Single purpose: Parse incoming raw payloads, apply SI conversion, update node/source state, and emit fast-path UI telemetry.
    - [DIP] Receives dependencies (AppState, GraphManager, SeriesExtractorPipeline) via constructor.
    """

    # Fast Path signal for real-time UI graphs
    data_processed = pyqtSignal(dict)

    def __init__(
        self,
        app_state: AppState,
        graph_manager: GraphManager,
        series_extractor: Optional[SeriesExtractorPipeline] = None
    ):
        super().__init__()
        self.app_state = app_state
        self.graph_manager = graph_manager
        self.series_extractor = series_extractor or SeriesExtractorPipeline()
        self.logger = logging.getLogger(__name__)

    @pyqtSlot(str, object)
    def handle_data_flow(self, source_id: str, payload: Any) -> None:
        """
        Extracts numerical values from raw payloads, converts to SI units,
        and updates AppState and GraphManager memory.
        """
        if not source_id:
            return

        # 1. Fetch DataSource metadata for fast-path extraction and conversion rule
        source = None
        get_all_ds_fn = getattr(self.app_state, "get_all_data_sources", None)
        all_sources = get_all_ds_fn() if callable(get_all_ds_fn) else []
        for s in (all_sources or []):
            if getattr(s, "id", None) == source_id or getattr(s, "name", None) == source_id:
                source = s
                break
        get_ds_fn = getattr(self.app_state, "get_data_source", None)
        if source is None and callable(get_ds_fn):
            source = get_ds_fn(source_id)
        get_dev_fn = getattr(self.app_state, "get_source_by_device_id", None)
        if source is None and callable(get_dev_fn):
            source = get_dev_fn(source_id)
        if source is None and all_sources:
            ext_clean = str(source_id).lower().replace("_", "").replace("-", "")
            for s in all_sources:
                s_name = str(getattr(s, "name", "") or "").lower().replace("_", "").replace("-", "")
                if s_name and (s_name in ext_clean or ext_clean in s_name):
                    source = s
                    break

        if source is not None and getattr(source, "id", None):
            source_id = source.id

        if source and getattr(source, "status", None) == SourceStatus.REJECTED:
            return

        meta = source.metadata if (source and isinstance(source.metadata, dict)) else {}
        extraction_path = meta.get("extraction_path")
        rule_id = meta.get("conversion_rule", 5)

        raw_val = 0.0
        try:
            if extraction_path and isinstance(extraction_path, list) and isinstance(payload, dict):
                # O(1) direct path traversal
                curr = payload
                found = True
                for p in extraction_path:
                    if isinstance(curr, dict) and p in curr:
                        curr = curr[p]
                    else:
                        found = False
                        break
                if found and isinstance(curr, (int, float)):
                    raw_val = float(curr)
                elif found and isinstance(curr, (list, tuple)):
                    raw_val = float(len(curr))
                else:
                    raw_val = float(self.series_extractor._parse_item(payload))
            elif isinstance(payload, (int, float)):
                raw_val = float(payload)
            elif isinstance(payload, dict) and "value" in payload and isinstance(payload["value"], (int, float)):
                raw_val = float(payload["value"])
            else:
                raw_val = float(self.series_extractor._parse_item(payload))
        except Exception:
            raw_val = 0.0

        # 2. Mathematical SI conversion (m/s, veh/s)
        val_si = SensorUnitConverter.convert(raw_val, rule_id)
        if val_si is None:
            # Discard reading to prevent model/filter hallucination
            self.logger.warning(
                f"[DataFlowRouter] ⚠️ Discarded payload from '{source_id}': "
                f"unconvertible rule_id={rule_id} for raw value={raw_val}. Preventing hallucination."
            )
            return

        # Update source in AppState
        if source:
            source.latest_value = val_si
            source.last_update = time.time()
        else:
            for src in (all_sources or []):
                if getattr(src, "id", None) == source_id:
                    src.latest_value = val_si
                    src.last_update = time.time()
                    break

        # Update Graph Node Memory with clean SI measurement
        self.graph_manager.update_node_memory(source_id, val_si, raw_payload=payload)

        # Resolve dynamic loss, drift and quality from updated nodes
        current_loss = 0.008
        current_drift = 0.012
        get_elems_fn = getattr(self.app_state, "get_elements_for_source", None)
        get_edge_fn = getattr(self.app_state, "get_edge", None)
        element_ids = get_elems_fn(source_id) if callable(get_elems_fn) else []
        node_losses = []
        node_drifts = []
        for eid in element_ids:
            if eid in self.graph_manager.nodes:
                node = self.graph_manager.nodes[eid]
                node_losses.append(getattr(node.state, "last_loss", 0.008))
                node_drifts.append(getattr(node.state, "last_psi", 0.012))
            else:
                target_edge = get_edge_fn(eid) if callable(get_edge_fn) else None
                if target_edge:
                    for nid in (target_edge.from_node, target_edge.to_node):
                        if nid in self.graph_manager.nodes:
                            node = self.graph_manager.nodes[nid]
                            node_losses.append(getattr(node.state, "last_loss", 0.008))
                            node_drifts.append(getattr(node.state, "last_psi", 0.012))
        if node_losses:
            current_loss = float(sum(node_losses) / len(node_losses))
        if node_drifts:
            current_drift = float(sum(node_drifts) / len(node_drifts))

        from src.engine.inference_engine import compute_telemetry_quality
        current_quality = compute_telemetry_quality(current_loss)

        # Emit Fast Path sensor telemetry for live UI state and health table
        self.data_processed.emit({
            "id": source_id,
            "raw": raw_val,
            "value": val_si,
            "loss": current_loss,
            "drift": current_drift,
            "quality": current_quality,
            "qualities": {source_id: current_quality},
            "losses": {source_id: current_loss},
            "drift_scores": {source_id: current_drift},
        })

    @pyqtSlot(str, object)
    def process_data_point(self, source_id: str, payload: Any) -> None:
        """External command entrypoint for manual data injection."""
        self.handle_data_flow(source_id, payload)
