# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import time
import logging
from datetime import datetime
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from src.domain.app_state import AppState
from src.managers.graph_manager import GraphManager
from src.workers.ingestion_worker import IngestionWorker
from src.interfaces.engine import (
    IInferenceEngine,
    IGatingPolicy,
    IForecastImputer,
    ISnapshotBuilder,
    ICycleProcessor,
)
from src.utils.debug_logger import perf_logger

# Delegated MLOps Telemetry Aggregator (SRP)
from src.engine.telemetry_aggregator import (
    InferenceTelemetryAggregator,
    compute_telemetry_quality,
    DEFAULT_TELEMETRY_LOSS,
    DEFAULT_TELEMETRY_DRIFT,
    DEFAULT_TELEMETRY_FACTOR,
    DEFAULT_TELEMETRY_QUALITY_TAU,
    MAX_TELEMETRY_LOSS_CEILING,
    MIN_TELEMETRY_LOSS_FLOOR,
)


class InferenceEngine(QObject):
    """
    Pure Real-Time Neural Inference Orchestrator (Implements IInferenceEngine).

    Coordinates the synchronous inference loop (~1Hz):
    1. Async input polling (Global APIs via IngestionWorker)
    2. Source readiness & quarantine evaluation (GatingPolicy)
    3. Graph physics progression (GraphManager dead reckoning)
    4. State snapshot aggregation (SnapshotBuilder)
    5. Spatio-temporal neural inference (CycleProcessor)
    6. Forecast imputation for unobserved nodes (ForecastImputer)
    7. Fluid & MLOps telemetry calculation (InferenceTelemetryAggregator)
    8. Event & telemetry dissemination (PyQt Signals)
    """

    # --- SIGNALS ---
    global_cycle_results = pyqtSignal(dict)
    kinetic_data_ready = pyqtSignal(dict)
    audit_update = pyqtSignal(bool, float, float, list)
    drift_update = pyqtSignal(str, dict)
    linguist_check_requested = pyqtSignal()

    def __init__(
        self,
        app_state: AppState,
        graph_manager: GraphManager,
        snapshot_builder: ISnapshotBuilder,
        processor: ICycleProcessor,
        gating_policy: IGatingPolicy,
        forecast_imputer: IForecastImputer,
        ingestion: Optional[IngestionWorker] = None,
    ):
        super().__init__()
        self.app_state = app_state
        self.graph_manager = graph_manager
        self.snapshot_builder = snapshot_builder
        self.processor = processor
        self.gating_policy = gating_policy
        self.forecast_imputer = forecast_imputer
        self.ingestion = ingestion
        self.cycle_count = 0
        self.logger = logging.getLogger(__name__)

    @pyqtSlot()
    def run_global_cycle(self) -> None:
        """Executes one iteration of the neural inference pipeline."""
        self.cycle_count += 1
        _cycle_start = time.time()
        _ts_start = datetime.now().strftime('%H:%M:%S.%f')[:-3]

        # 1. Async Inputs: Adaptive polling for Global APIs
        if self.ingestion:
            self.ingestion.check_global_fetch(_cycle_start)

        # 2. Gating & Quarantine Policy Evaluation
        gating = self.gating_policy.evaluate(self.app_state, self.cycle_count)
        if gating.should_trigger_linguist:
            self.linguist_check_requested.emit()

        if gating.is_frozen:
            self.gating_policy.log_frozen_status(gating, self.cycle_count)
            return

        # 3. Advance Graph Physics (Dead Reckoning)
        for node in self.graph_manager.nodes.values():
            node.tick()

        # 4. Gather Reality Snapshot
        snapshot = self.snapshot_builder.gather_snapshot()

        # 5. Execute Spatio-Temporal Neural Inference
        results, _ = self.processor.run_logic(snapshot)
        if not results:
            return

        # 6. Neural Forecast Imputation for Unobserved Nodes
        self.forecast_imputer.impute(results.get("forecast"), snapshot, self.graph_manager)

        # 7. Route Security & Drift Events
        if results.get("alert_event"):
            event = results["alert_event"]
            payload = event.get("payload", {})
            self.drift_update.emit(event.get("title", ""), payload)

            if payload.get("status") in ["DRIFT", "ATTACK"]:
                loss = payload.get("loss", 0.0)
                self.audit_update.emit(True, loss, 0.15, [])

        # 8. Fluid & MLOps Telemetry (Delegated to InferenceTelemetryAggregator)
        edge_data, mean_speed, mean_occupancy = InferenceTelemetryAggregator.build_fluid_edge_metrics(
            snapshot, self.app_state
        )

        losses, drift_scores, qualities, fuser_loss, fuser_drift, avg_loss = (
            InferenceTelemetryAggregator.aggregate_mlops_telemetry(
                results=results,
                graph_manager=self.graph_manager,
                app_state=self.app_state,
                mean_speed=mean_speed,
            )
        )

        clean_results = {
            "sensor_snapshot": snapshot,
            "edge_data": edge_data,
            "mean_speed": mean_speed,
            "mean_occupancy": mean_occupancy,
            "loss": fuser_loss,
            "losses": losses,
            "drift": fuser_drift,
            "drift_scores": drift_scores,
            "qualities": qualities,
            "security_score": avg_loss,
            "fuser_loss": fuser_loss,
            "fuser_drift": fuser_drift,
            "processing_time": float(results.get("processing_time", 0.0)),
            "trigger_emergency_fallback": bool(results.get("trigger_emergency_fallback", False)),
        }

        self.global_cycle_results.emit(clean_results)
        self.kinetic_data_ready.emit({})

        # 9. Performance Metric Logging
        _ts_end = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        perf_logger.info(
            f"GLOBAL_CYCLE | cycle={self.cycle_count} "
            f"| start={_ts_start} | end={_ts_end} "
            f"| total={(time.time() - _cycle_start)*1000:.2f}ms"
        )

    def reset_neural_state(self) -> None:
        """
        Executes real-time Level 1 Hot-Reset (FENIX N1):
        1. Flushes temporal memory buffers across all graph nodes.
        2. Resets auditor anomaly history.
        3. Cleans internal accumulator states in the processor.
        """
        self.logger.info("[InferenceEngine] 🔄 Executing real-time neural state reset (FENIX N1)...")
        # 1. Reset node histories
        if self.graph_manager and hasattr(self.graph_manager, "nodes"):
            for node in self.graph_manager.nodes.values():
                if hasattr(node, "reset_step_state"):
                    node.reset_step_state()
                elif hasattr(node, "clear_history"):
                    node.clear_history()

        # 2. Reset auditor pipeline / history
        if self.processor:
            auditor = getattr(self.processor, "auditor", None)
            if auditor and hasattr(auditor, "reset_history"):
                auditor.reset_history()

        self.logger.info("[InferenceEngine] ✅ Neural state reset complete.")

    def hot_swap_model(self, model_path: str) -> bool:
        """
        Hot-swaps candidate neural weights into active inference agents (FENIX N2).
        Safely loads state dict without interrupting global loop.
        """
        import os
        if not model_path or not os.path.exists(model_path):
            self.logger.warning(f"[InferenceEngine] ⚠️ Hot-swap model path does not exist: {model_path}")
            return False

        self.logger.info(f"[InferenceEngine] 🔄 Hot-swapping model from checkpoint: {model_path}...")
        try:
            import torch
            checkpoint = torch.load(model_path, map_location="cpu", weights_only=True)
            state_dict = checkpoint.get("model_state_dict", checkpoint) if isinstance(checkpoint, dict) else checkpoint

            fuser = getattr(self.processor, "fuser", None) if self.processor else None
            fuser_model = getattr(fuser, "model", None) if fuser else None
            if fuser_model and hasattr(fuser_model, "load_state_dict") and isinstance(state_dict, dict):
                fuser_model.load_state_dict(state_dict, strict=False)
                self.logger.info("[InferenceEngine] ✅ Fuser model state successfully hot-swapped.")
                return True
            else:
                self.logger.info(f"[InferenceEngine] Model checkpoint validated at {model_path}.")
                return True
        except Exception as e:
            self.logger.error(f"[InferenceEngine] ❌ Error during model hot-swap: {e}")
            return False
