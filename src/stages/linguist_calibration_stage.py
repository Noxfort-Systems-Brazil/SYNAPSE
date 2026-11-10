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

        ontology_path = shared_context.get("ontology_checkpoint_path")
        if not ontology_path:
            config_dir = shared_context.get("config_dir", "")
            ontology_path = os.path.join(config_dir, "ontology.safetensors")

        has_checkpoint = bool(checkpoint_path and os.path.exists(checkpoint_path) and os.path.getsize(checkpoint_path) > 0)
        has_ontology = bool(ontology_path and os.path.exists(ontology_path) and os.path.getsize(ontology_path) > 0)

        # ── SKIP LOCK / WARM START ──
        if has_checkpoint and has_ontology:
            self.log("[LinguistCalibrationStage] 🏆 Calibrated checkpoint and ontology found. Skipping training.")
            self.progress(85)
            return True

        if has_checkpoint and not has_ontology and golden_path and os.path.exists(golden_path):
            self.log("[LinguistCalibrationStage] 💡 Checkpoint exists, but ontology.safetensors is missing. Generating ontology...")
            try:
                df = pd.read_parquet(golden_path)
                self._generate_and_save_ontology(ontology_path, df)
                self.progress(85)
                return True
            except Exception as e:
                self.log(f"[LinguistCalibrationStage] ⚠️ Failed generating ontology: {e}")

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

            # ── BUILD & PERSIST ONTOLOGY SAFETENSORS ──
            self._generate_and_save_ontology(ontology_path, df)

            self.progress(88)
            return True

        except Exception as e:
            self.log(f"[LinguistCalibrationStage] ❌ Calibration failed: {e}")
            logger.exception("Linguist calibration failed")
            return True  # Non-fatal to allow downstream stages to attempt execution

    def _generate_and_save_ontology(self, ontology_path: str, df: pd.DataFrame) -> None:
        """Extracts and serializes ModernBERT semantic concepts to ontology.safetensors."""
        from src.infrastructure.safetensors_repository import SafetensorsRepository
        from src.models.modernbert import ModernBertEmbeddingModel
        from src.utils.model_paths import get_modernbert_path
        from transformers import AutoTokenizer
        import torch
        import torch.nn.functional as F

        try:
            model_path = get_modernbert_path()
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=os.path.isdir(model_path))
            model = ModernBertEmbeddingModel(model_name=model_path).to(device)
            model.eval()

            def embed_texts(texts: List[str]) -> torch.Tensor:
                encoded = tokenizer(texts, padding=True, truncation=True, return_tensors="pt").to(device)
                with torch.no_grad():
                    device_type = "cuda" if device.type == "cuda" else "cpu"
                    with torch.autocast(device_type=device_type, dtype=torch.float16 if device_type == "cuda" else torch.bfloat16):
                        pooled = model(encoded["input_ids"], encoded["attention_mask"])
                emb = torch.mean(pooled, dim=0, keepdim=True)
                return F.normalize(emb, p=2, dim=1).contiguous().cpu()

            tensors: Dict[str, torch.Tensor] = {}

            # Canonical modality definitions
            modality_descriptions = {
                "Vehicle Count": ["vehicle count", "camera detection", "contagem veicular", "detected vehicles", "intensity_val"],
                "Traffic Flow": ["traffic flow", "vehicle flow", "fluxo de tráfego", "veículos por hora", "flow_val"],
                "Vehicle Speed": ["vehicle speed", "velocidade média", "radar speed", "speed_val", "current speed kmh"],
                "Traffic Density": ["traffic density", "densidade de tráfego", "veículos por km", "occupancy", "ocupação viária"],
            }

            for mod_name, desc_texts in modality_descriptions.items():
                tensors[f"modality_{mod_name.lower().replace(' ', '_')}"] = embed_texts(desc_texts)

            # Historical sensors detected in the Golden dataset
            if "sensor_id" in df.columns:
                detected_sensors = [s for s in df["sensor_id"].dropna().unique().tolist() if str(s).strip()]
                for sid in detected_sensors:
                    sensor_texts = [f"sensor id {sid}", f"traffic sensor {sid}"]
                    for s_id, col, mod in self.SENSOR_MODALITY_MAPPING:
                        if sid == s_id:
                            sensor_texts.extend([f"{mod} measurement", f"sensor column {col}"])
                    tensors[f"sensor_{sid}"] = embed_texts(sensor_texts)

            repo = SafetensorsRepository(logger=logger)
            if os.path.exists(ontology_path) and os.path.getsize(ontology_path) > 0:
                existing = repo.load_tensors(ontology_path)
                for k, v in existing.items():
                    if k not in tensors:
                        tensors[k] = v

            os.makedirs(os.path.dirname(os.path.abspath(ontology_path)), exist_ok=True)
            saved = repo.save_tensors(tensors, ontology_path)
            if saved:
                self.log(f"[LinguistCalibrationStage] 📚 Generated and saved ontology: {ontology_path} ({len(tensors)} concepts)")
        except Exception as e:
            self.log(f"[LinguistCalibrationStage] ⚠️ Failed to generate ontology.safetensors: {e}")
            logger.warning(f"Could not generate ontology.safetensors: {e}")
