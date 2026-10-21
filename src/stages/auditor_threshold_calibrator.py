# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import shutil
import logging
from typing import Any
import torch
import numpy as np

logger = logging.getLogger("Synapse.Stages.AuditorThresholdCalibrator")


class AuditorThresholdCalibrator:
    """Calculates statistical anomaly thresholds and persists calibrated state."""

    @staticmethod
    def calibrate_threshold(
        agent: Any,
        windows: np.ndarray,
        batch_size: int = 64,
        calibration_percentile: float = 99,
        safety_headroom: float = 1.35,
        min_threshold_floor: float = 0.75,
    ) -> float:
        agent.model.eval()
        device = getattr(agent.pipeline, "device", getattr(agent, "device", torch.device("cpu")))
        calibrator = getattr(agent.pipeline, "calibrator", getattr(agent.trainer, "calibrator", None))
        physics_engine = getattr(agent.pipeline, "physics_engine", getattr(agent.trainer, "physics_engine", None))
        physics_weight = getattr(agent.pipeline, "physics_weight", getattr(agent, "physics_weight", 0.5))
        enable_pinn = getattr(agent.pipeline, "enable_pinn", getattr(agent, "enable_pinn", True))

        all_scores = []

        with torch.no_grad():
            for i in range(0, len(windows), batch_size):
                batch = torch.tensor(
                    windows[i:i + batch_size], dtype=torch.float32
                ).to(device)

                from src.utils.normalization import TensorNormalizer
                batch = TensorNormalizer.sanitize(batch)
                batch, _, _ = TensorNormalizer.instance_norm(batch)
                batch = TensorNormalizer.sanitize(batch)

                feats, z, rec_feats, time_recon = agent.model(batch, return_time_recon=True)
                feats = feats.to(device)
                z = z.to(device)
                rec_feats = rec_feats.to(device)
                time_recon = time_recon.to(device)

                rec_err = torch.mean((rec_feats - feats) ** 2, dim=1)
                time_err = torch.mean((time_recon - batch) ** 2, dim=1)

                if calibrator is not None and calibrator.center is not None:
                    center = calibrator.center.to(device)
                    dist_center = torch.sum((z - center) ** 2, dim=1)
                else:
                    dist_center = torch.zeros(batch.shape[0], device=device)

                if physics_engine is not None and enable_pinn:
                    physics_res = physics_engine.compute_losses(time_recon, orig_x=batch)
                    phys_val = physics_res.get("total_physics_loss", torch.tensor(0.0, device=device))
                    if isinstance(phys_val, torch.Tensor):
                        phys_val = phys_val.to(device)
                else:
                    phys_val = torch.tensor(0.0, device=device)

                scores = rec_err + (0.5 * time_err) + (0.1 * dist_center) + (physics_weight * phys_val)
                all_scores.append(scores.cpu())

        if all_scores:
            all_scores = torch.cat(all_scores).numpy()
            valid_scores = all_scores[np.isfinite(all_scores)]
            if len(valid_scores) > 0:
                raw_pct = float(np.percentile(valid_scores, calibration_percentile))
                calibrated_threshold = max(min_threshold_floor, raw_pct * safety_headroom)
            else:
                calibrated_threshold = min_threshold_floor
        else:
            calibrated_threshold = min_threshold_floor

        # Override threshold with the statistical one in calibrator and model
        if calibrator is not None:
            calibrator.threshold = calibrated_threshold
        agent.model.threshold = torch.tensor(calibrated_threshold)
        if getattr(agent, "threshold", None) is not None:
            agent.threshold = torch.tensor(calibrated_threshold)

        return calibrated_threshold

    @staticmethod
    def save_checkpoint(agent: Any, checkpoint_path: str, window_size: int = 60) -> None:
        """Saves the full calibrated state using atomic file write and vault sync."""
        os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)

        calibrator = getattr(agent.pipeline, "calibrator", getattr(agent.trainer, "calibrator", None))
        center = calibrator.center if (calibrator and calibrator.center is not None) else getattr(agent.model, 'center', None)
        if isinstance(center, torch.Tensor):
            center = center.detach().float()
        center_init = calibrator.center_initialized if calibrator else getattr(agent.model, 'center_initialized', False)
        threshold = calibrator.threshold if calibrator else getattr(agent.model, 'threshold', 0.5)
        if isinstance(threshold, torch.Tensor):
            threshold = threshold.item()

        scat = getattr(agent.model, 'scattering', None)
        j_val = getattr(agent.model, 'J', getattr(scat, 'J', 2))
        q_val = getattr(agent.model, 'Q', getattr(scat, 'Q', 1))
        if isinstance(q_val, (tuple, list)):
            q_val = q_val[0]

        state = {
            'model_state_dict': agent.model.state_dict(),
            'threshold': threshold,
            'center': center,
            'center_initialized': center_init,
            'input_len': getattr(agent.model, 'input_len', window_size),
            'latent_dim': getattr(agent.model, 'latent_dim', 16),
            'J': int(j_val),
            'Q': int(q_val),
        }

        temp_path = checkpoint_path + ".tmp"
        torch.save(state, temp_path)
        shutil.move(temp_path, checkpoint_path)

        try:
            from src.managers.storage_manager import StorageManager
            sm = StorageManager()
            sm.sync_file_to_vault(checkpoint_path)
        except Exception:
            pass
