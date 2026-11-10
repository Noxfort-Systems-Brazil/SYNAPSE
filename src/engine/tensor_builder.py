# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import torch
import numpy as np
import torch.nn.functional as F
from typing import Dict, Any, Optional, Tuple

from src.utils.logging_setup import logger
from src.managers.graph_manager import GraphManager

class TensorBuilder:
    """
    Responsible for dynamically extracting and shaping Graph state features into PyTorch Tensors.
    Adheres to the Single Responsibility Principle (SRP) by isolating data casting from Business Logic.
    
    Refactored V4 (Zero-Allocation Pinned Buffers & Cached Topology):
    - Reuses page-locked (pinned) host buffers across 1Hz cycles to eliminate per-node tensor allocations.
    - Extracts Observability Mask (M in {0, 1}^N) for dynamic anchor calibration.
    - Extracts Global Velocity vectors for macroscopic boundary conditioning.
    """
    
    TARGET_SEQ_LEN = 60

    def __init__(self, device: torch.device, coordinator_model: Any, graph_manager: GraphManager):
        self.device = device
        self.graph_manager = graph_manager
        
        # Determine expected dimension via Introspection (Decoupled from Engine)
        self.expected_dim = self._inspect_dimension(coordinator_model)

        # Reusable pre-allocated host buffers (resized automatically if topology changes)
        self._buf_key: Optional[Tuple[int, int, int, bool]] = None
        self._spatial_cpu: Optional[torch.Tensor] = None
        self._temporal_cpu: Optional[torch.Tensor] = None
        self._mask_cpu: Optional[torch.Tensor] = None
        self._vel_cpu: Optional[torch.Tensor] = None

        # Cached device edge_index
        self._cached_edge_ref: Optional[torch.Tensor] = None
        self._cached_edge_key: Optional[Tuple[Any, ...]] = None
        self._cached_edge_dev: Optional[torch.Tensor] = None

    def _inspect_dimension(self, coordinator_model: Any) -> int:
        """Dynamically looks at the GAT model to cast padding constraints."""
        expected_dim = 32  # DEFAULTS TO 32 (TCN Latent Dim)
        try:
            conv1 = getattr(coordinator_model, "conv1", None)
            if conv1 is not None:
                in_channels = getattr(conv1, "in_channels", None)
                if isinstance(in_channels, tuple):
                    expected_dim = in_channels[0]
                elif isinstance(in_channels, int):
                    expected_dim = in_channels
                logger.info(f"[TensorBuilder] Extracted Expected Input Dim = {expected_dim}")
            else:
                logger.warning(f"[TensorBuilder] Unknown Coordinator structure. Using default dim={expected_dim}.")
        except Exception as e:
            logger.warning(f"[TensorBuilder] Dimension inspection failed: {e}. Defaulting to {expected_dim}.")
            
        return expected_dim

    def _ensure_buffers(self, num_nodes: int, target_len: int) -> bool:
        use_pin = (self.device.type == "cuda") and torch.cuda.is_available()
        key = (num_nodes, self.expected_dim, target_len, use_pin)
        if self._buf_key != key:
            self._spatial_cpu = torch.empty((num_nodes, self.expected_dim), dtype=torch.float32, pin_memory=use_pin)
            self._temporal_cpu = torch.empty((target_len, num_nodes), dtype=torch.float32, pin_memory=use_pin)
            self._mask_cpu = torch.empty(num_nodes, dtype=torch.float32, pin_memory=use_pin)
            self._vel_cpu = torch.empty(num_nodes, dtype=torch.float32, pin_memory=use_pin)
            self._buf_key = key
        return use_pin

    def _resolve_device_edge_index(self) -> torch.Tensor:
        raw_edge_idx = getattr(self.graph_manager, "edge_index", None)
        if raw_edge_idx is None:
            return torch.empty((2, 0), dtype=torch.long, device=self.device)
        if isinstance(raw_edge_idx, torch.Tensor):
            e_key = (
                raw_edge_idx.data_ptr(),
                raw_edge_idx.shape,
                raw_edge_idx.device,
                raw_edge_idx._version,
                self.device,
            )
            if self._cached_edge_key == e_key and self._cached_edge_dev is not None:
                return self._cached_edge_dev
            dev_edges = raw_edge_idx.to(self.device, non_blocking=(self.device.type == "cuda"))
            self._cached_edge_ref = raw_edge_idx
            self._cached_edge_key = e_key
            self._cached_edge_dev = dev_edges
            return dev_edges
        return torch.as_tensor(raw_edge_idx, dtype=torch.long, device=self.device)

    def prepare_tensors(self, snapshot: Dict[str, Any]) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Transforms raw node data into uniformly padded tensors, observability masks, and global velocities safely
        using pre-allocated contiguous buffers and asynchronous DMA transfers.
        """
        ordered_ids = self.graph_manager.get_ordered_node_ids()
        if not ordered_ids:
            raise ValueError("No data available for tensor construction.")

        num_nodes = len(ordered_ids)
        target_len = self.TARGET_SEQ_LEN
        use_pin = self._ensure_buffers(num_nodes, target_len)

        spatial_np = self._spatial_cpu.numpy()   # type: ignore[union-attr]
        temporal_np = self._temporal_cpu.numpy() # type: ignore[union-attr]
        mask_np = self._mask_cpu.numpy()         # type: ignore[union-attr]
        vel_np = self._vel_cpu.numpy()           # type: ignore[union-attr]

        spatial_np.fill(0.0)
        temporal_np.fill(0.0)

        # Extract macroscopic speed baseline from global APIs (TomTom / Waze) if available
        macro_speed = 0.0
        app_state = getattr(self.graph_manager, "app_state", None)
        get_all_ds_fn = getattr(app_state, "get_all_data_sources", None) if app_state else None
        if callable(get_all_ds_fn):
            global_speeds = []
            for src in (get_all_ds_fn() or []):
                if not getattr(src, "is_local", True):
                    raw_val = getattr(src, "latest_value", 0.0)
                    v = 0.0
                    if isinstance(raw_val, (int, float)):
                        v = float(raw_val)
                    elif isinstance(raw_val, dict):
                        v_cand = raw_val.get("speed") or raw_val.get("currentSpeed_kmh") or raw_val.get("value")
                        try:
                            v = float(v_cand) if v_cand is not None else 0.0
                        except (ValueError, TypeError):
                            v = 0.0
                    else:
                        try:
                            v = float(raw_val or 0.0)
                        except (ValueError, TypeError):
                            v = 0.0

                    if v > 0.0:
                        global_speeds.append(v)
            if global_speeds:
                macro_speed = float(np.mean(global_speeds))

        expected_dim = self.expected_dim
        for idx, nid in enumerate(ordered_ids):
            node_data = snapshot.get(nid, {}) if snapshot else {}
            
            # Observability Mask (1.0 = Ground truth live sensor, 0.0 = Virtual/Synthesized node)
            raw_v = node_data.get("value", 0.0)
            val_float = float(raw_v) if isinstance(raw_v, (int, float)) else 0.0
            node_type = node_data.get("type")
            node_status = node_data.get("status")
            if node_type in ("synthetic", "virtual") or node_status in ("Ghost", "Extrapolated", "Synthesized"):
                is_real = False
            else:
                is_real = (node_type == "real") or (node_status == "Active") or (val_float > 0.0)
            mask_np[idx] = 1.0 if is_real else 0.0
            vel_np[idx] = macro_speed if macro_speed > 0.0 else val_float
            
            # Spatial Embedding (X) filled in-place
            if node_data and "embedding" in node_data:
                emb = node_data["embedding"]
                if isinstance(emb, torch.Tensor):
                    emb_arr = emb.detach().cpu().numpy().reshape(-1)
                elif isinstance(emb, np.ndarray):
                    emb_arr = emb.reshape(-1)
                elif isinstance(emb, list):
                    emb_arr = np.asarray(emb, dtype=np.float32).reshape(-1)
                else:
                    emb_arr = None

                if emb_arr is not None and emb_arr.size > 0:
                    copy_dim = min(expected_dim, emb_arr.size)
                    spatial_np[idx, :copy_dim] = emb_arr[:copy_dim]

            # Temporal History filled in-place (right-aligned when shorter than target_len)
            node_obj = self.graph_manager.get_node(nid)
            if node_obj is not None:
                hist = node_obj.memory.get_numpy().reshape(-1)
                h_len = hist.size
                if h_len >= target_len:
                    temporal_np[:, idx] = hist[-target_len:]
                elif h_len > 0:
                    temporal_np[target_len - h_len :, idx] = hist

        edge_index = self._resolve_device_edge_index()

        if use_pin:
            x_spatial = self._spatial_cpu.to(self.device, non_blocking=True)         # type: ignore[union-attr]
            x_temporal = self._temporal_cpu.to(self.device, non_blocking=True)       # type: ignore[union-attr]
            observability_mask = self._mask_cpu.to(self.device, non_blocking=True)   # type: ignore[union-attr]
            global_velocities = self._vel_cpu.to(self.device, non_blocking=True)     # type: ignore[union-attr]
        else:
            x_spatial = self._spatial_cpu.clone().to(self.device)                    # type: ignore[union-attr]
            x_temporal = self._temporal_cpu.clone().to(self.device)                  # type: ignore[union-attr]
            observability_mask = self._mask_cpu.clone().to(self.device)              # type: ignore[union-attr]
            global_velocities = self._vel_cpu.clone().to(self.device)                # type: ignore[union-attr]
        
        return x_spatial, edge_index, x_temporal, observability_mask, global_velocities
