# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import torch
import numpy as np
from typing import Dict, Any, Optional

from src.stages.base_stage import BaseStage
from src.agents.auditor_agent import AuditorAgent
from src.utils.convergence_tracker import MarginalConvergenceTracker
from src.stages.auditor_window_preparer import AuditorWindowPreparer
from src.stages.auditor_threshold_calibrator import AuditorThresholdCalibrator


class AuditorCalibrationStage(BaseStage):
    """
    Auditor Calibration Stage — Cold-Start Elimination.
    
    Trains the AuditorAgent (WaveletAEOCC) on the Golden Dataset during
    the Offline Phase, so it enters the Online Phase fully calibrated.
    
    Pipeline Position: Runs AFTER ClassificationStage (requires golden_v1.parquet).
    
    Outputs:
    - auditor_calibrated.pth: Model weights + threshold + center
    """

    # Training Defaults (Dynamic Marginal Convergence)
    MAX_SAFETY_EPOCHS = 100
    MIN_EPOCHS = 5
    PATIENCE = 4
    MIN_DELTA = 1e-4
    SLOPE_THRESHOLD = 1e-4
    BATCH_SIZE = 64
    WINDOW_SIZE = 60  # Matches default seq_len used by NeuralFactory
    CALIBRATION_PERCENTILE = 99
    SAFETY_HEADROOM = 1.35
    MIN_THRESHOLD_FLOOR = 0.75

    def execute(self, shared_context: Dict[str, Any]) -> bool:
        """Trains the Auditor on golden data and saves calibrated checkpoint."""
        checkpoint_path = shared_context.get("auditor_checkpoint_path")
        golden_path = shared_context.get("golden_path")

        # ── SKIP LOCK ──
        if checkpoint_path and os.path.exists(checkpoint_path) and os.path.getsize(checkpoint_path) > 0:
            self.log("[AuditorCalibrationStage] 🏆 Calibrated checkpoint found. Skipping training.")
            self.progress(95)
            return True

        # ── VALIDATE GOLDEN ──
        if not golden_path or not os.path.exists(golden_path):
            self.log("[AuditorCalibrationStage] ⚠️ Golden dataset not found. Skipping calibration.")
            return True  # Non-fatal: system can still run with uncalibrated auditor

        if self.check_interruption():
            return False

        self.log("[AuditorCalibrationStage] 🏋️ Training Auditor on Golden Dataset (Dynamic Marginal Convergence)...")

        try:
            # 1. Load & Prepare Data
            windows = self._prepare_windows(golden_path)
            if windows is None or len(windows) == 0:
                self.log("[AuditorCalibrationStage] ⚠️ No valid training windows. Skipping.")
                return True

            self.log(f"[AuditorCalibrationStage] 📊 Prepared {len(windows)} training windows (size={self.WINDOW_SIZE}).")

            # 2. Create Agent (Load Phase Zero Hparams if available)
            aud_cfg: Dict[str, Any] = {}
            hparams_candidates = [
                os.path.join(self.synapse_root, "Checkpoint", "best_hparams.pth"),
                os.path.join("checkpoints", "best_hparams.pth"),
            ]
            for hp_path in hparams_candidates:
                if os.path.exists(hp_path):
                    try:
                        hp_all = torch.load(hp_path, map_location="cpu")
                        if isinstance(hp_all, dict):
                            aud_cfg = hp_all.get("auditor", {}) if isinstance(hp_all.get("auditor"), dict) else hp_all
                        break
                    except Exception:
                        pass

            j_val = int(aud_cfg.get("J", aud_cfg.get("auditor_J", 2)))
            q_val = int(aud_cfg.get("Q", aud_cfg.get("auditor_Q", 1)))
            latent_val = int(aud_cfg.get("latent_dim", aud_cfg.get("auditor_latent", 16)))
            lr_val = float(aud_cfg.get("lr", aud_cfg.get("learning_rate", 1e-3)))

            agent = AuditorAgent(
                input_len=self.WINDOW_SIZE,
                J=j_val, Q=q_val, latent_dim=latent_val,
                learning_rate=lr_val
            )

            # 3. Dynamic Training Loop
            tracker = MarginalConvergenceTracker(
                min_epochs=self.MIN_EPOCHS,
                max_epochs=self.MAX_SAFETY_EPOCHS,
                patience=self.PATIENCE,
                min_delta=self.MIN_DELTA,
                slope_threshold=self.SLOPE_THRESHOLD,
                restore_best_weights=True
            )

            self.log(f"[AuditorCalibrationStage] 🔄 Starting dynamic calibration (max={self.MAX_SAFETY_EPOCHS}, min={self.MIN_EPOCHS})...")
            
            for epoch in range(self.MAX_SAFETY_EPOCHS):
                if self.check_interruption():
                    return False

                epoch_losses = []
                indices = np.random.permutation(len(windows))

                for i in range(0, len(indices), self.BATCH_SIZE):
                    batch_idx = indices[i:i + self.BATCH_SIZE]
                    batch = torch.tensor(windows[batch_idx], dtype=torch.float32)
                    loss = agent.train_step(batch)
                    epoch_losses.append(loss)

                avg_loss = float(np.mean(epoch_losses))
                
                # Log telemetry
                if (epoch + 1) % 5 == 0 or epoch == 0:
                    self.log(f"[AuditorCalibrationStage]   Epoch {epoch+1} — Loss: {avg_loss:.6f}")

                # Check dynamic marginal convergence
                should_stop = tracker.step(epoch=epoch, loss=avg_loss, model=agent.model)

                # Dynamic progress scaling (80 to 90 range)
                progress_val = min(90, 80 + int(((epoch + 1) / max(20, epoch + 5)) * 10))
                self.progress(progress_val)

                if should_stop:
                    self.log(
                        f"[AuditorCalibrationStage] 🛑 Converged at epoch {epoch+1} "
                        f"({tracker.stop_reason}) | Best Loss: {tracker.best_loss:.6f}"
                    )
                    break

            # 4. Calibrate Threshold
            self.log("[AuditorCalibrationStage] 📐 Calibrating anomaly threshold (percentile 99 + safety headroom)...")
            self._calibrate_threshold(agent, windows)

            # 5. Save Checkpoint
            self._save_checkpoint(agent, checkpoint_path)

            thresh_val = float(agent.model.threshold.item() if isinstance(agent.model.threshold, torch.Tensor) else agent.model.threshold)
            self.log(f"[AuditorCalibrationStage] ✅ Auditor calibrated successfully!")
            self.log(f"[AuditorCalibrationStage] 📊 Final threshold: {thresh_val:.6f}")
            self.progress(95)

            return True

        except Exception as e:
            self.log(f"[AuditorCalibrationStage] ❌ Calibration failed: {e}")
            import traceback
            traceback.print_exc()
            return True  # Non-fatal: don't break the pipeline

    def _prepare_windows(self, golden_path: str) -> Optional[np.ndarray]:
        """Loads Golden Dataset and prepares feature windows."""
        return AuditorWindowPreparer.prepare_windows(golden_path, window_size=self.WINDOW_SIZE)

    def _calibrate_threshold(self, agent: AuditorAgent, windows: np.ndarray):
        """Runs validation on all training windows to set data-driven threshold."""
        return AuditorThresholdCalibrator.calibrate_threshold(
            agent=agent,
            windows=windows,
            batch_size=self.BATCH_SIZE,
            calibration_percentile=self.CALIBRATION_PERCENTILE,
            safety_headroom=self.SAFETY_HEADROOM,
            min_threshold_floor=self.MIN_THRESHOLD_FLOOR,
        )

    def _save_checkpoint(self, agent: AuditorAgent, checkpoint_path: str):
        """Saves the full calibrated state using CheckpointService pattern."""
        AuditorThresholdCalibrator.save_checkpoint(agent, checkpoint_path, window_size=self.WINDOW_SIZE)
        self.log(f"[AuditorCalibrationStage] 💾 Checkpoint saved: {checkpoint_path}")
