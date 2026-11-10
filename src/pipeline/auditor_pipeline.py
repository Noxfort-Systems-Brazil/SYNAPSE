# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import torch
import numpy as np
import logging
from collections import deque
from typing import Dict, Any, Union, Optional
from torch.amp import autocast

from src.models.wavelet_ae_occ import WaveletSpectralAE, WaveletAEOCC
from src.strategies.deep_svdd_calibrator import DeepSVDDCalibrator
from src.physics.traffic_loss import TrafficPhysicsLoss
from src.utils.normalization import TensorNormalizer

logger = logging.getLogger("Synapse.AuditorPipeline")


class AuditorPipeline:
    """
    Dedicated Neural Pipeline for Security Auditing and Anomaly Detection.
    Encapsulates Wavelet Scattering Autoencoder, Deep SVDD Calibrator, and PINN physics evaluation.
    
    Includes M-of-N persistence tracking and catastrophic physics violation triggering
    for activating Autonomous Fallback Bridge (AFB) and Protocolo Fênix N1.
    """

    def __init__(
        self,
        model: Optional[WaveletSpectralAE] = None,
        calibrator: Optional[DeepSVDDCalibrator] = None,
        physics_engine: Optional[TrafficPhysicsLoss] = None,
        input_len: int = 60,
        J: int = 2,
        Q: int = 1,
        latent_dim: int = 16,
        physics_weight: float = 0.5,
        max_acceleration: float = 10.0,
        enable_pinn: bool = True,
        device: Optional[torch.device] = None,
        window_size: int = 10,
        persistence_threshold: int = 7
    ):
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.physics_weight = physics_weight
        self.enable_pinn = enable_pinn

        # --- Resilience Tracking (M-of-N Rule & Catastrophic Violation) ---
        self.window_size = window_size
        self.persistence_threshold = persistence_threshold
        self._anomaly_history: deque = deque(maxlen=window_size)
        self._consecutive_catastrophic: int = 0

        if model is not None:
            self.model = model
        else:
            padded_len = 2 ** int(np.ceil(np.log2(input_len)) + 1)
            max_safe_j = int(np.log2(padded_len))
            if J > max_safe_j:
                safe_J = max(1, max_safe_j)
                if J > safe_J:
                    logger.info(f"[AuditorPipeline] Auto-adjusting J from {J} to {safe_J} for stability (padded_len={padded_len}).")
                J = safe_J

            self.model = WaveletSpectralAE(
                input_len=input_len,
                J=J,
                Q=Q,
                latent_dim=latent_dim
            )

        self.calibrator = calibrator or DeepSVDDCalibrator(latent_dim=latent_dim)
        self.physics_engine = physics_engine or TrafficPhysicsLoss(max_acceleration=max_acceleration)

        self.model.to(self.device)

    def reset_history(self):
        """Resets anomaly sliding window after Fênix N1 Hot-Reset."""
        self._anomaly_history.clear()
        dyn_cal = getattr(self.calibrator, "dynamic_calibrator", None)
        if dyn_cal is not None:
            try:
                dyn_cal.reset()
            except Exception:
                pass
        logger.info("[AuditorPipeline] Anomaly history and dynamic calibrator reset.")

    def to(self, device: Any) -> 'AuditorPipeline':
        self.device = torch.device(device) if isinstance(device, str) else device
        self.model.to(self.device)
        return self

    @staticmethod
    def _as_scalar_tensor(val: Any, device: torch.device) -> torch.Tensor:
        if isinstance(val, torch.Tensor):
            return val.to(device=device, dtype=torch.float32).mean()
        return torch.tensor(float(val), device=device, dtype=torch.float32)

    def audit_async(self, input_data: Union[Dict[str, Any], torch.Tensor]) -> Dict[str, Any]:
        """
        Enqueues Wavelet-SVDD-PINN auditing kernels on the active CUDA stream without CPU synchronization.
        """
        self.model.eval()

        if isinstance(input_data, dict):
            x = input_data.get("signature")
            if x is None:
                x = input_data.get("data")
            if x is None:
                x = input_data.get("window")
            if x is None:
                return {"error": "No data provided"}
            x = torch.tensor(x, dtype=torch.float32) if not isinstance(x, torch.Tensor) else x
        else:
            x = input_data if isinstance(input_data, torch.Tensor) else torch.tensor(input_data, dtype=torch.float32)

        x = x.to(self.device)
        if x.ndim == 1:
            x = x.unsqueeze(0)

        target_len = getattr(self.model, 'input_len', None)
        if isinstance(target_len, int):
            sig_dim = x.shape[1]
            if sig_dim != target_len:
                if sig_dim < target_len:
                    import torch.nn.functional as F
                    if sig_dim >= 1:
                        x = F.pad(x.unsqueeze(1), (0, target_len - sig_dim), mode='replicate').squeeze(1)
                    else:
                        x = F.pad(x, (0, target_len - sig_dim))
                else:
                    x = x[:, :target_len]

        x = TensorNormalizer.sanitize(x)
        x, _, _ = TensorNormalizer.instance_norm(x)
        x = TensorNormalizer.sanitize(x)
        device_type = self.device.type if self.device.type != 'mps' else 'cpu'

        with torch.no_grad():
            with autocast(device_type=device_type, enabled=(self.device.type == 'cuda')):
                feats, z, rec_feats, time_recon = self.model(x, return_time_recon=True)

                feats = feats.to(x.device)
                z = z.to(x.device)
                rec_feats = rec_feats.to(x.device)
                time_recon = time_recon.to(x.device)

                rec_err = torch.mean((rec_feats - feats) ** 2, dim=1)
                time_err = torch.mean((time_recon - x) ** 2, dim=1)

                dist_center, _ = self.calibrator.compute_anomaly_scores(z)
                if isinstance(dist_center, torch.Tensor):
                    dist_center = dist_center.to(x.device)

                physics_res = self.physics_engine.compute_losses(time_recon, orig_x=x)
                physics_loss = physics_res["total_physics_loss"] if self.enable_pinn else torch.tensor(0.0, device=x.device)
                if isinstance(physics_loss, torch.Tensor):
                    physics_loss = physics_loss.to(x.device)

                total_score = rec_err + (0.5 * time_err) + (0.1 * dist_center) + (self.physics_weight * physics_loss)
                dev = x.device
                metrics_gpu = torch.stack([
                    self._as_scalar_tensor(total_score, dev),
                    total_score.reshape(-1)[0].to(device=dev, dtype=torch.float32),
                    self._as_scalar_tensor(rec_err, dev),
                    self._as_scalar_tensor(time_err, dev),
                    self._as_scalar_tensor(dist_center, dev),
                    self._as_scalar_tensor(physics_loss, dev),
                    self._as_scalar_tensor(physics_res["loss_bounds"], dev),
                    self._as_scalar_tensor(physics_res["loss_kinematics"], dev),
                    self._as_scalar_tensor(physics_res["loss_smooth"], dev),
                    self._as_scalar_tensor(physics_res["loss_conservation"], dev),
                ])
                return {"metrics_gpu": metrics_gpu, "numel": int(total_score.numel())}

    def finalize_audit(self, async_pack: Dict[str, Any]) -> Dict[str, Any]:
        """Unpacks GPU audit scalars in a single D2H transfer and updates M-of-N / Fênix N1 resilience."""
        if "error" in async_pack:
            return async_pack

        (
            score_val,
            first_score_val,
            rec_val,
            time_val,
            dist_val,
            physics_val,
            bounds_val,
            kin_val,
            smooth_val,
            cons_val,
        ) = [float(v) for v in async_pack["metrics_gpu"].detach().cpu().tolist()]

        dyn_cal = getattr(self.calibrator, "dynamic_calibrator", None)
        if dyn_cal is not None:
            try:
                eval_res = dyn_cal.evaluate(score_val)
                if isinstance(eval_res, tuple) and len(eval_res) >= 2:
                    is_anomaly_val = bool(eval_res[0])
                    threshold = float(eval_res[1])
                else:
                    threshold = float(getattr(self.calibrator, "threshold", 1.0))
                    is_anomaly_val = bool(score_val > threshold)
            except Exception:
                threshold = float(getattr(self.calibrator, "threshold", 1.0))
                is_anomaly_val = bool(score_val > threshold)
        else:
            raw_thresh = getattr(self.calibrator, "threshold", 1.0)
            threshold = float(raw_thresh.item() if isinstance(raw_thresh, torch.Tensor) else raw_thresh)
            cmp_val = score_val if async_pack.get("numel", 1) == 1 else first_score_val
            is_anomaly_val = bool(cmp_val > threshold)

        is_catastrophic = (
            np.isnan(score_val) or np.isinf(score_val) or
            (physics_val > (5.0 * max(threshold, 1.0))) or
            (score_val > (10.0 * max(threshold, 1.0)))
        )

        if is_catastrophic:
            self._consecutive_catastrophic += 1
        else:
            self._consecutive_catastrophic = 0

        self._anomaly_history.append(1 if is_anomaly_val else 0)
        persistent_anomaly_count = sum(self._anomaly_history)

        trigger_emergency_fallback = (
            self._consecutive_catastrophic >= 2 or
            (len(self._anomaly_history) >= 5 and persistent_anomaly_count >= self.persistence_threshold)
        )

        if trigger_emergency_fallback:
            logger.critical(
                f"[AuditorPipeline] 🚨 EMERGENCY FALLBACK TRIGGERED! "
                f"(Catastrophic consecutive: {self._consecutive_catastrophic}, "
                f"Persistence: {persistent_anomaly_count}/{len(self._anomaly_history)})"
            )

        return {
            "is_anomaly": is_anomaly_val,
            "score": score_val,
            "threshold": threshold,
            "spectral_residual": rec_val,
            "time_residual": time_val,
            "compactness_dist": dist_val,
            "physics_residual": physics_val,
            "trigger_emergency_fallback": trigger_emergency_fallback,
            "consecutive_catastrophic": self._consecutive_catastrophic,
            "persistence_ratio": persistent_anomaly_count / max(1, len(self._anomaly_history)),
            "physics_details": {
                "bounds_loss": bounds_val,
                "kinematics_loss": kin_val,
                "smooth_loss": smooth_val,
                "conservation_loss": cons_val,
            },
            "status": "audited"
        }

    def audit(self, input_data: Union[Dict[str, Any], torch.Tensor]) -> Dict[str, Any]:
        """Reconstructs the embedding and signal to audit for anomalies (spectral, statistical, physical)."""
        return self.finalize_audit(self.audit_async(input_data))
