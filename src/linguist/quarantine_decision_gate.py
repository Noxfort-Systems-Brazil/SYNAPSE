# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: src/linguist/quarantine_decision_gate.py
# Author: Gabriel Moraes
# Date: 2026-09-14

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
    ):
        self.app_state = app_state
        self.sample_chunk_size = sample_chunk_size
        self.max_attempts = max_attempts
        self.grammar_loss_threshold = grammar_loss_threshold
        self.learning_attempts: Dict[str, int] = {}
        self.calibrated_thresholds: Dict[str, Any] = {}
        
        self._load_calibrated_thresholds(calibration_path)

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

    def get_required_samples(self, source_id: str) -> int:
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

