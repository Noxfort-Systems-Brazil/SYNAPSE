# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
import numpy as np
import pandas as pd

from src.stages.base_stage import BaseStage
from src.agents.linguist_agent import LinguistAgent

logger = logging.getLogger("Synapse.Stages.LinguistCalibrationStage")


class LinguistCalibrationStage(BaseStage):
    """
    Linguist Calibration Stage — Data-Driven PINN Threshold Derivation.
    
    Samples historical traffic series from the Golden Dataset (golden_v1.parquet)
    across discrete modalities (Vehicle Count, Vehicle Speed, Traffic Flow) and measures
    the empirical PINN loss distribution (Reconstruction + Physics Residuals).
    
    Calculates safety-headroom thresholds per modality and persists them to:
    data/config/linguist_calibrated.json
    
    Eliminates rigid, static constants (e.g. 0.5) in the Quarantine Decision Gate.
    """

    DEFAULT_HEADROOM = 1.35
    DEFAULT_FLOOR = 1.50
    CALIBRATION_PERCENTILE = 95
    MAX_SAMPLES_PER_SENSOR = 6

    SENSOR_MODALITY_MAPPING = [
        ("cam_01", "intensity_val", "Vehicle Count"),
        ("loop_01", "flow_val", "Traffic Flow"),
        ("tomtom", "speed_val", "Vehicle Speed"),
        ("waze", "flow_val", "Traffic Flow"),
    ]

    def execute(self, shared_context: Dict[str, Any]) -> bool:
        """Calibrates Linguist PINN loss thresholds from the golden dataset."""
        checkpoint_path = shared_context.get("linguist_checkpoint_path")
        golden_path = shared_context.get("golden_path")

        if not checkpoint_path:
            config_dir = shared_context.get("config_dir", "")
            checkpoint_path = os.path.join(config_dir, "linguist_calibrated.json")

        # ── SKIP LOCK / WARM START ──
        if checkpoint_path and os.path.exists(checkpoint_path) and os.path.getsize(checkpoint_path) > 0:
            self.log("[LinguistCalibrationStage] 🏆 Calibrated checkpoint found. Skipping training.")
            self.progress(85)
            return True

        # ── VALIDATE GOLDEN DATASET ──
        if not golden_path or not os.path.exists(golden_path):
            self.log("[LinguistCalibrationStage] ⚠️ Golden dataset not found. Skipping calibration.")
            return True

        if self.check_interruption():
            return False

        self.log("[LinguistCalibrationStage] 🔬 Calibrating Linguist PINN on Golden Dataset...")

        try:
            df = pd.read_parquet(golden_path)
            modality_losses: Dict[str, List[float]] = {}

            for sensor_id, col, modality in self.SENSOR_MODALITY_MAPPING:
                if self.check_interruption():
                    return False

                if "sensor_id" not in df.columns or col not in df.columns:
                    continue

                sub = df[df["sensor_id"] == sensor_id]
                if sub.empty:
                    continue

                series = sub[col].dropna().values
                if len(series) < 10:
                    continue

                losses = []
                step = max(1, (len(series) - 10) // self.MAX_SAMPLES_PER_SENSOR)
                for start in range(0, min(len(series) - 10, step * self.MAX_SAMPLES_PER_SENSOR), step):
                    if self.check_interruption():
                        return False

                    agent = LinguistAgent(sensor_id=f"calib_{sensor_id}_{start}")
                    chunk = series[start:start + 10].tolist()
                    loss_val = agent.train_step(chunk, epochs=10, semantic_type=modality)
                    if np.isfinite(loss_val):
                        losses.append(loss_val)

                if modality not in modality_losses:
                    modality_losses[modality] = []
                modality_losses[modality].extend(losses)

                self.log(
                    f"[LinguistCalibrationStage]   Sensor '{sensor_id}' ({modality}) evaluated: "
                    f"{len(losses)} windows tested."
                )

            # Compute thresholds
            modalities_calibrated: Dict[str, float] = {}
            for mod, losses in modality_losses.items():
                if losses:
                    p95 = float(np.percentile(losses, self.CALIBRATION_PERCENTILE))
                    thresh = max(self.DEFAULT_FLOOR, p95 * self.DEFAULT_HEADROOM)
                    modalities_calibrated[mod] = round(thresh, 4)
                else:
                    modalities_calibrated[mod] = self.DEFAULT_FLOOR

            # Fallback for unrepresented modality
            modalities_calibrated.setdefault("Traffic Density", 2.0)

            default_thresh = round(max(modalities_calibrated.values()) * 1.05, 4)

            calibration_payload = {
                "calibrated_at": datetime.now().isoformat(),
                "sample_chunk_size": 5,
                "calibration_percentile": self.CALIBRATION_PERCENTILE,
                "safety_headroom": self.DEFAULT_HEADROOM,
                "default_grammar_threshold": default_thresh,
                "modalities": modalities_calibrated,
            }

            os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
            with open(checkpoint_path, "w", encoding="utf-8") as f:
                json.dump(calibration_payload, f, indent=2)

            self.log(f"[LinguistCalibrationStage] 💾 Calibration saved: {checkpoint_path}")
            self.log(f"[LinguistCalibrationStage] 📊 Default grammar threshold: {default_thresh:.4f}")
            for mod, val in modalities_calibrated.items():
                self.log(f"[LinguistCalibrationStage]   • {mod}: {val:.4f}")

            self.progress(88)
            return True

        except Exception as e:
            self.log(f"[LinguistCalibrationStage] ❌ Calibration failed: {e}")
            logger.exception("Linguist calibration failed")
            return True  # Non-fatal to allow downstream stages to attempt execution
