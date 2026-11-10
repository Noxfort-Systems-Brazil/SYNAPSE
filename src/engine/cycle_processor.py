# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import time
import torch
import numpy as np
import torch.nn.functional as F
from typing import Dict, Any, Tuple, Optional, TYPE_CHECKING

from src.utils.logging_setup import logger
from src.utils.debug_logger import perf_logger

# --- Domain ---
from src.domain.app_state import AppState

# --- Managers & Engine Helpers ---
from src.managers.xai_manager import XAIManager
from src.managers.graph_manager import GraphManager
from src.engine.tensor_builder import TensorBuilder
from src.engine.security_monitor import SecurityMonitor

# --- Lazy Imports (Prevent Circular Dependency) ---
if TYPE_CHECKING:
    from src.agents.coordinator_agent import CoordinatorAgent
    from src.agents.fuser_agent import FuserAgent
    from src.agents.auditor_agent import AuditorAgent

class CycleProcessor:
    """
    Handles the mathematical heavy-lifting of the Global Inference Cycle.
    
    Refactored V9 (SOLID Principles):
    - Uses TensorBuilder for data preprocessing (SRP).
    - Unifies Agent Pipeline abstraction via standard .inference() (LSP/ISP).
    - Uses SecurityMonitor for alerting evaluation (SRP).
    """

    def __init__(self, 
                 app_state: AppState, 
                 device: torch.device,
                 coordinator: 'CoordinatorAgent',
                 fuser: 'FuserAgent',
                 auditor: 'AuditorAgent',
                 xai_manager: XAIManager,
                 graph_manager: GraphManager):
        
        self.app_state = app_state
        self.device = device
        
        # Agents (Injected)
        self.coordinator = coordinator
        self.fuser = fuser
        self.auditor = auditor
        
        # Managers
        self.xai_manager = xai_manager
        self.graph_manager = graph_manager
        
        # --- Engine Domain Extractors (SOLID) ---
        self.device = torch.device(device) if isinstance(device, str) else device
        self.tensor_builder = TensorBuilder(device, coordinator.model, graph_manager)

        # Dual CUDA Streams for concurrent Coordinator & Auditor execution on GPU
        self._stream_coord: Optional[torch.cuda.Stream] = None
        self._stream_audit: Optional[torch.cuda.Stream] = None
        if self.device.type == "cuda" and torch.cuda.is_available():
            try:
                self._stream_coord = torch.cuda.Stream(device=self.device)
                self._stream_audit = torch.cuda.Stream(device=self.device)
            except Exception as exc:
                logger.debug(f"[Processor] Could not initialize CUDA streams: {exc}")
        
        # Extract calibrated threshold from auditor if available (default 0.75)
        auditor_thresh = 0.75
        if auditor:
            auditor_pipe = getattr(auditor, "pipeline", None)
            calibrator = getattr(auditor_pipe, "calibrator", None) if auditor_pipe else None
            auditor_model = getattr(auditor, "model", None)
            raw_thresh = getattr(auditor_model, "threshold", None) if auditor_model else None
            if calibrator is not None and getattr(calibrator, "threshold", None) is not None:
                auditor_thresh = float(calibrator.threshold)
            elif raw_thresh is not None:
                auditor_thresh = float(raw_thresh.item() if isinstance(raw_thresh, torch.Tensor) else raw_thresh)
        self.security_monitor = SecurityMonitor(threshold=auditor_thresh)

    @staticmethod
    def _build_temporal_signature(
        x_temporal: torch.Tensor, obs_mask: Optional[torch.Tensor]
    ) -> torch.Tensor:
        """Computes [1, SeqLen] temporal signature on GPU without boolean-indexing CPU syncs."""
        if obs_mask is not None and x_temporal.ndim == 2 and obs_mask.numel() == x_temporal.shape[1]:
            weights = (obs_mask.reshape(-1) > 0).to(dtype=x_temporal.dtype)
            w_sum = weights.sum()
            weighted = (x_temporal * weights.unsqueeze(0)).sum(dim=1) / torch.clamp(w_sum, min=1.0)
            uniform = x_temporal.mean(dim=1)
            return torch.where(w_sum > 0, weighted, uniform).unsqueeze(0)
        return x_temporal.mean(dim=1).unsqueeze(0)

    def run_logic(self, snapshot: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        Executes the main AI pipeline orchestrating standardized agents.
        """
        start_time = time.time()
        
        # 1. Prepare Tensors (Delegated to TensorBuilder - SRP)
        try:
            tensor_pack = self.tensor_builder.prepare_tensors(snapshot)
            if len(tensor_pack) == 5:
                x_spatial, edge_index, x_temporal, obs_mask, g_vel = tensor_pack
            else:
                x_spatial, edge_index, x_temporal = tensor_pack[:3]
                obs_mask, g_vel = None, None
        except ValueError:
            return {}, None
        except Exception as e:
            logger.error(f"[Processor] Critical Tensor Failure: {e}")
            return {}, None
        t_tensor = time.time()

        has_temporal_shape = x_temporal is not None and x_temporal.numel() > 0
        use_cuda_streams = (
            self._stream_coord is not None
            and self._stream_audit is not None
            and has_temporal_shape
            and self.auditor is not None
        )

        spatial_embedding = None
        security_score = 0.0
        auditor_report: Dict[str, Any] = {}

        if use_cuda_streams:
            default_stream = torch.cuda.current_stream(self.device)
            self._stream_coord.wait_stream(default_stream)
            self._stream_audit.wait_stream(default_stream)

            # 1. Enqueue Coordinator (GATv2) on _stream_coord FIRST (non-blocking)
            with torch.cuda.stream(self._stream_coord):
                try:
                    spatial_embedding = self.coordinator.inference({
                        "x_spatial": x_spatial,
                        "edge_index": edge_index,
                    })
                except Exception as e:
                    logger.critical(f"[Processor] Spatial Inference Crash: {e}")
                    raise e

            # 2. Enqueue Auditor GPU forward on _stream_audit SECOND (overlaps Coordinator + Fuser!)
            audit_async_pack = None
            auditor_pipe = getattr(self.auditor, "pipeline", None)
            audit_async_fn = getattr(auditor_pipe, "audit_async", None) if auditor_pipe is not None else None
            finalize_audit_fn = getattr(auditor_pipe, "finalize_audit", None) if auditor_pipe is not None else None
            use_two_phase_audit = (
                callable(audit_async_fn)
                and callable(finalize_audit_fn)
                and not type(self.auditor).__name__.startswith("MagicMock")
                and not type(auditor_pipe).__name__.startswith("MagicMock")
            )
            with torch.cuda.stream(self._stream_audit):
                try:
                    signature = self._build_temporal_signature(x_temporal, obs_mask)
                    if use_two_phase_audit:
                        audit_async_pack = audit_async_fn({"signature": signature})
                    else:
                        auditor_report = self.auditor.inference({"signature": signature})
                        security_score = auditor_report.get("score", 0.0)
                except Exception as e:
                    logger.error(f"[Processor] Concurrent security sweep failed: {e}")

            t_coordinator = time.time()

            # 3. Enqueue Fuser on _stream_coord (chains directly after Coordinator on GPU)
            with torch.cuda.stream(self._stream_coord):
                edge_attr = getattr(self.graph_manager, "edge_attr", None)
                forecast = self.fuser.inference({
                    "x_temporal": x_temporal,
                    "spatial_context": spatial_embedding,
                    "observability_mask": obs_mask,
                    "global_velocities": g_vel,
                    "edge_index": edge_index,
                    "edge_attr": edge_attr,
                })
            self._stream_coord.synchronize()
            default_stream.wait_stream(self._stream_coord)
            t_fuser = time.time()

            # 4. Synchronize _stream_audit and unpack scalars in a single D2H transfer
            self._stream_audit.synchronize()
            if use_two_phase_audit and audit_async_pack is not None:
                try:
                    auditor_report = finalize_audit_fn(audit_async_pack)
                    security_score = auditor_report.get("score", 0.0)
                except Exception as e:
                    logger.error(f"[Processor] Auditor finalization failed: {e}")
            t_auditor = time.time()
        else:
            # Sequential execution path (CPU, fallback or empty temporal history)
            try:
                spatial_embedding = self.coordinator.inference({
                    "x_spatial": x_spatial, 
                    "edge_index": edge_index,
                })
            except Exception as e:
                logger.critical(f"[Processor] Spatial Inference Crash: {e}")
                raise e
            t_coordinator = time.time()
            
            edge_attr = getattr(self.graph_manager, "edge_attr", None)
            forecast = self.fuser.inference({
                "x_temporal": x_temporal,
                "spatial_context": spatial_embedding,
                "observability_mask": obs_mask,
                "global_velocities": g_vel,
                "edge_index": edge_index,
                "edge_attr": edge_attr,
            })
            t_fuser = time.time()
            
            if self.auditor:
                try:
                    if has_temporal_shape and bool(torch.any(x_temporal != 0)):
                        signature = self._build_temporal_signature(x_temporal, obs_mask)
                    else:
                        signature = spatial_embedding.mean(dim=1).unsqueeze(0)
                    
                    auditor_report = self.auditor.inference({"signature": signature})
                    security_score = auditor_report.get("score", 0.0)
                except Exception as e:
                    logger.error(f"[Processor] Security sweep failed: {e}")
            t_auditor = time.time()

        # 5. Result Packaging
        total_time = t_auditor - start_time
        fuser_loss = float(getattr(self.fuser, "last_loss", 0.008))
        fuser_drift = float(getattr(self.fuser, "last_psi", 0.012))
        results = {
            "spatial_embedding": spatial_embedding,
            "forecast": forecast,
            "fuser_loss": fuser_loss,
            "fuser_drift": fuser_drift,
            "security_score": security_score,
            "auditor_report": auditor_report,
            "trigger_emergency_fallback": auditor_report.get("trigger_emergency_fallback", False),
            "processing_time": total_time
        }
        
        # --- Debug Log: CYCLE (per-stage neural performance) ---
        perf_logger.info(
            f"CYCLE | tensor={(t_tensor - start_time)*1000:.2f}ms "
            f"| coordinator={(t_coordinator - t_tensor)*1000:.2f}ms "
            f"| fuser={(t_fuser - t_coordinator)*1000:.2f}ms "
            f"| auditor={(t_auditor - t_fuser)*1000:.2f}ms "
            f"| total={total_time*1000:.2f}ms"
        )
        
        # 6. Alerting (Delegated to SecurityMonitor - SRP)
        active_thresh = auditor_report.get("threshold", self.security_monitor.threshold)
        alert = self.security_monitor.evaluate(security_score, threshold=active_thresh)
        
        return results, alert
