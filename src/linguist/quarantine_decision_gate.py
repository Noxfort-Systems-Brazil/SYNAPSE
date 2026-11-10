# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

from src.domain.entities import DataSource, SourceStatus

logger = logging.getLogger("Synapse.Linguist.QuarantineDecisionGate")


class QuarantineDecisionGate:
    """
    Manages learning attempts, decision thresholds, promotion, and rejection of quarantined sources.
    Supports dynamic, empirical thresholds derived from the Golden Dataset (linguist_calibrated.json).
    """

    def __init__(
        self,
        app_state: Any,
        sample_chunk_size: int = 5,
        max_attempts: int = 2,
        grammar_loss_threshold: float = 2.5,
        calibration_path: Optional[str] = None,
        ontology_path: Optional[str] = None,
    ):
        self.app_state = app_state
        self.sample_chunk_size = sample_chunk_size
        self.max_attempts = max_attempts
        self.grammar_loss_threshold = grammar_loss_threshold
        self.learning_attempts: Dict[str, int] = {}
        self.calibrated_thresholds: Dict[str, Any] = {}
        
        self._load_calibrated_thresholds(calibration_path)
        self.ontology_path = ontology_path or self._resolve_ontology_path()
        self.ontology_tensors: Dict[str, Any] = {}
        self._load_ontology()

    def _resolve_ontology_path(self) -> str:
        env_path = os.environ.get("SYNAPSE_ONTOLOGY_PATH")
        if env_path:
            return env_path
        from src.storage.path_scaffolder import PathScaffolder
        return PathScaffolder().get_config_file("ontology.safetensors")

    def _load_ontology(self) -> None:
        """Loads learned semantic concepts from ontology.safetensors if present."""
        if self.ontology_path and os.path.exists(self.ontology_path) and os.path.getsize(self.ontology_path) > 0:
            try:
                from safetensors.torch import load_file
                self.ontology_tensors = load_file(self.ontology_path)
                logger.info(f"📚 [DecisionGate] Loaded {len(self.ontology_tensors)} ontology concepts from {self.ontology_path}")
            except Exception as e:
                logger.warning(f"⚠️ [DecisionGate] Could not load ontology from {self.ontology_path}: {e}")

    def is_fast_path_eligible(self, source: DataSource) -> bool:
        """
        Determines if a sensor can bypass full quarantine (Fast-Path).
        A sensor is eligible if:
        1. It is cataloged with valid semantic type, unit, and positive confidence score.
        2. Its concept/modality or sensor ID exists in the loaded ontology.safetensors.
        """
        if not self.ontology_tensors:
            return False

        has_semantic = bool(source.semantic_type and source.inferred_unit and (source.confidence_score or 0.0) >= 0.80)
        if not has_semantic:
            return False

        sensor_key = f"sensor_{source.id}"
        mod_key = f"modality_{str(source.semantic_type).lower().replace(' ', '_')}"
        return bool(sensor_key in self.ontology_tensors or mod_key in self.ontology_tensors)

    def _load_calibrated_thresholds(self, path: Optional[str] = None):
        """Loads data-driven thresholds calibrated from the Golden Dataset if available."""
        target_path = None
        if path and os.path.exists(path):
            target_path = Path(path)
        else:
            env_path = os.environ.get("SYNAPSE_CALIBRATION_PATH")
            if env_path and os.path.exists(env_path):
                target_path = Path(env_path)
            else:
                from src.storage.path_scaffolder import PathScaffolder
                candidate = Path(PathScaffolder().get_config_file("linguist_calibrated.json"))
                if candidate.exists() and candidate.stat().st_size > 0:
                    target_path = candidate

        if target_path:
            try:
                with open(target_path, "r", encoding="utf-8") as f:
                    self.calibrated_thresholds = json.load(f)
                
                default_th = self.calibrated_thresholds.get("default_grammar_threshold", self.grammar_loss_threshold)
                self.grammar_loss_threshold = default_th
                logger.info(
                    f"🎓 [DecisionGate] Loaded data-driven grammar thresholds from {target_path}: "
                    f"Default={default_th:.4f}, Modalities={self.calibrated_thresholds.get('modalities')}"
                )
            except Exception as e:
                logger.warning(f"⚠️ [DecisionGate] Could not load calibrated thresholds from {target_path}: {e}")

    def get_grammar_threshold(self, semantic_type: Optional[str] = None) -> float:
        """Returns the specific threshold for the given modality, or default."""
        if self.calibrated_thresholds and semantic_type:
            mods = self.calibrated_thresholds.get("modalities", {})
            sem_lower = semantic_type.lower()
            for mod_name, thresh in mods.items():
                if mod_name.lower() in sem_lower or sem_lower in mod_name.lower():
                    return float(thresh)
            if "default_grammar_threshold" in self.calibrated_thresholds:
                return float(self.calibrated_thresholds["default_grammar_threshold"])
        return self.grammar_loss_threshold

    def get_required_samples(self, source: Any) -> int:
        source_obj = source if isinstance(source, DataSource) else None
        if source_obj is None and hasattr(self.app_state, "get_source_by_device_id"):
            source_obj = self.app_state.get_source_by_device_id(str(source))

        if source_obj and self.is_fast_path_eligible(source_obj):
            return 1

        source_id = source_obj.id if source_obj else str(source)
        current_attempt = self.learning_attempts.get(source_id, 0)
        return self.sample_chunk_size * (current_attempt + 1)

    def handle_learning_failure(
        self,
        source: DataSource,
        pipeline: Any,
        loss: float,
        agent_factory: Any,
        semantic_type: Optional[str] = None
    ) -> None:
        attempts = self.learning_attempts.get(source.id, 0) + 1
        self.learning_attempts[source.id] = attempts
        threshold = self.get_grammar_threshold(semantic_type or source.semantic_type)

        if attempts >= self.max_attempts:
            logger.warning(
                f"❌ [DecisionGate] Falha na validação física/gramatical após 10 amostras ({attempts} tentativas). Sinal rejeitado."
            )
            self.reject_source(
                source,
                "Padrão não físico / Não convergência do PINN após 10 amostras.",
                agent_factory,
                pipeline=pipeline,
            )
        else:
            logger.info(
                f"⏳ [DecisionGate] Calibrando física do sinal (Perda PINN: {loss:.4f} >= Teto {threshold:.4f}). "
                f"Coletando mais +{self.sample_chunk_size} amostras (total até 10)..."
            )
            pipeline.extend_quarantine_buffer(source.id, self.sample_chunk_size)

    def promote_source(
        self,
        source: DataSource,
        pipeline: Any,
        data_np: np.ndarray,
        sem_type: str,
        unit: str,
        confidence: float,
        agent_factory: Any,
        update_signal: Any,
    ) -> None:
        source.status = SourceStatus.ACTIVE
        source.semantic_type = sem_type
        source.inferred_unit = unit
        source.confidence_score = confidence

        if len(data_np) > 0:
            source.latest_value = float(data_np[-1])
            self.app_state.update_source_value(source.id, source.latest_value)

        pipeline.promote_to_active(source.id)
        if update_signal:
            update_signal.emit(source.name, sem_type, confidence)

        self.persist_source_state(source)
        self._update_ontology_for_source(source, sem_type)

        if agent_factory is not None:
            agent_factory.release_linguist(source.id)
            logger.info(
                f"🛑 [DecisionGate] Agente Linguista de '{source.name}' ({source.id}) liberado da memória."
            )

        logger.info(
            f"🎉 [DecisionGate] 🟢 Sensor '{source.name}' ({source.id}) VALIDADO COM SUCESSO! Promovido para status ATIVO."
        )

        if source.id in self.learning_attempts:
            del self.learning_attempts[source.id]

    def reject_source(
        self,
        source: DataSource,
        reason: str,
        agent_factory: Any,
        pipeline: Optional[Any] = None,
    ) -> None:
        logger.error(f"[System] ⛔ Source '{source.name}' REJECTED. Reason: {reason}")
        source.status = SourceStatus.REJECTED
        self.learning_attempts[source.id] = 0
        self.persist_source_state(source)

        if pipeline is not None:
            pipeline.remove_source_context(source.id)

        if agent_factory is not None:
            agent_factory.release_linguist(source.id)

    def persist_source_state(self, source: DataSource) -> None:
        if self.app_state is not None:
            self.app_state.notify_source_updated(source)

    def _update_ontology_for_source(self, source: DataSource, sem_type: str) -> None:
        """Registers the promoted source into ontology.safetensors."""
        if not self.ontology_path:
            return

        sensor_key = f"sensor_{source.id}"
        mod_key = f"modality_{str(sem_type).lower().replace(' ', '_')}"
        if sensor_key in self.ontology_tensors:
            return

        try:
            from src.infrastructure.safetensors_repository import SafetensorsRepository
            from src.models.modernbert import ModernBertEmbeddingModel
            from src.utils.model_paths import get_modernbert_path
            from transformers import AutoTokenizer
            import torch
            import torch.nn.functional as F

            model_path = get_modernbert_path()
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=os.path.isdir(model_path))
            model = ModernBertEmbeddingModel(model_name=model_path).to(device)
            model.eval()

            texts = [f"sensor id {source.id}", f"{source.name}", f"modality {sem_type}"]
            encoded = tokenizer(texts, padding=True, truncation=True, return_tensors="pt").to(device)
            with torch.no_grad():
                device_type = "cuda" if device.type == "cuda" else "cpu"
                with torch.autocast(device_type=device_type, dtype=torch.float16 if device_type == "cuda" else torch.bfloat16):
                    pooled = model(encoded["input_ids"], encoded["attention_mask"])
            emb = torch.mean(pooled, dim=0, keepdim=True)
            norm_emb = F.normalize(emb, p=2, dim=1).contiguous().cpu()

            self.ontology_tensors[sensor_key] = norm_emb
            if mod_key not in self.ontology_tensors:
                self.ontology_tensors[mod_key] = norm_emb

            repo = SafetensorsRepository(logger=logger)
            os.makedirs(os.path.dirname(os.path.abspath(self.ontology_path)), exist_ok=True)
            repo.save_tensors(self.ontology_tensors, self.ontology_path)
            logger.info(f"💾 [DecisionGate] Updated ontology with '{source.name}' ({sensor_key}) at {self.ontology_path}")
        except Exception as e:
            logger.warning(f"⚠️ [DecisionGate] Could not update ontology for {source.id}: {e}")

