# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Auditor Checkpoint Loader (SOLID: SRP & DIP).

Responsible exclusively for locating, parsing, and applying offline-calibrated
weights and thresholds to the AuditorAgent, eliminating cold starts without
polluting the NeuralFactory or violating the Law of Demeter.
"""

import os
from typing import Dict, Any, List, Optional
import torch

from src.utils.logging_setup import get_logger

logger = get_logger("AuditorCheckpointLoader")


class AuditorCheckpointLoader:
    """
    Encapsulates checkpoint discovery, tensor shape metadata inspection,
    and state restoration for AuditorAgent.
    """

    def __init__(self, weights_dir: str = "checkpoints/"):
        self.weights_dir = weights_dir

    def get_checkpoint_candidates(self) -> List[str]:
        """Resolves candidate paths for the calibrated auditor model."""
        candidates = [
            os.path.join(self.weights_dir, "auditor_calibrated.pth"),
        ]
        
        env_dir = os.environ.get("SYNAPSE_CHECKPOINTS_DIR")
        if env_dir:
            candidates.insert(0, os.path.join(env_dir, "auditor_calibrated.pth"))

        from src.storage.path_scaffolder import PathScaffolder
        candidates.extend([
            PathScaffolder().get_config_file("auditor_calibrated.pth"),
            os.path.join("config", "auditor_calibrated.pth"),
        ])
        return candidates

    def peek_checkpoint_meta(self, candidates: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Inspects calibrated checkpoint metadata (J, Q, latent_dim, input_len)
        to prevent state_dict shape mismatches before building AuditorAgent.
        """
        paths = candidates or self.get_checkpoint_candidates()
        for path in paths:
            if os.path.exists(path) and os.path.getsize(path) > 500:
                try:
                    ckpt = torch.load(path, map_location="cpu", weights_only=False)
                    if not isinstance(ckpt, dict):
                        continue
                    meta: Dict[str, Any] = {}
                    for k in ("input_len", "latent_dim", "J", "Q"):
                        if k in ckpt and ckpt[k] is not None:
                            meta[k] = int(ckpt[k])
                    
                    # Infer/verify J from encoder.0.weight input dimension
                    if "model_state_dict" in ckpt:
                        sd = ckpt["model_state_dict"]
                        w0 = sd.get("encoder.0.weight")
                        if isinstance(w0, torch.Tensor) and w0.ndim >= 2:
                            scat_dim = int(w0.shape[1])
                            if scat_dim == 3:
                                meta["J"] = 1
                            elif scat_dim == 4:
                                meta["J"] = 2
                        w3 = sd.get("encoder.3.weight")
                        if isinstance(w3, torch.Tensor) and w3.ndim >= 1:
                            meta["latent_dim"] = int(w3.shape[0])
                        td3 = sd.get("time_decoder.3.weight")
                        if isinstance(td3, torch.Tensor) and td3.ndim >= 1:
                            meta["input_len"] = int(td3.shape[0])
                    return meta
                except Exception as e:
                    logger.debug(f"Error peeking metadata from {path}: {e}")
                    continue
        return {}

    def load_calibration(self, auditor: Any, candidates: Optional[List[str]] = None) -> bool:
        """
        Loads offline-calibrated state into the AuditorAgent via its public interface.
        Returns True if a valid checkpoint was loaded, False otherwise.
        """
        paths = candidates or self.get_checkpoint_candidates()
        for path in paths:
            if os.path.exists(path) and os.path.getsize(path) > 500:
                try:
                    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
                    if not isinstance(checkpoint, dict):
                        continue

                    model_sd = checkpoint.get("model_state_dict")
                    threshold = checkpoint.get("threshold")
                    center = checkpoint.get("center")
                    center_init = checkpoint.get("center_initialized", True)

                    apply_cal_fn = getattr(auditor, "apply_calibration", None)
                    auditor_model = getattr(auditor, "model", None)
                    if callable(apply_cal_fn):
                        apply_cal_fn(
                            model_state_dict=model_sd,
                            threshold=threshold,
                            center=center,
                            center_initialized=center_init,
                        )
                    elif auditor_model is not None:
                        # Fallback for mock or legacy objects
                        if model_sd is not None:
                            auditor_model.load_state_dict(model_sd)
                        if threshold is not None:
                            auditor_model.threshold = torch.tensor(float(threshold))

                    loaded_thresh = 0.0
                    raw_thresh = getattr(auditor_model, "threshold", None) if auditor_model is not None else None
                    if raw_thresh is not None:
                        loaded_thresh = float(raw_thresh.item() if isinstance(raw_thresh, torch.Tensor) else raw_thresh)

                    logger.info(
                        f"Auditor loaded CALIBRATED checkpoint from {path} (threshold={loaded_thresh:.6f})"
                    )
                    return True

                except Exception as e:
                    logger.warning(f"Failed to load auditor checkpoint {path}: {e}")

        # Fallback if no offline checkpoint: initialize with robust dynamic floor
        safe_floor = 0.85
        set_default_fn = getattr(auditor, "set_default_threshold", None)
        auditor_model = getattr(auditor, "model", None)
        if callable(set_default_fn):
            set_default_fn(safe_floor)
        elif auditor_model is not None and getattr(auditor_model, "threshold", None) is not None:
            auditor_model.threshold = torch.tensor(safe_floor)

        logger.info(
            f"No offline auditor calibration found. Using dynamic baseline floor ({safe_floor})."
        )
        return False
