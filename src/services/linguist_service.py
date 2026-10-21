# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: src/services/linguist_service.py
# Author: Gabriel Moraes
# Date: 2026-08-20

from typing import Dict, Optional, List, Any
import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot

from src.domain.app_state import AppState
from src.domain.entities import SourceStatus, DataSource, MapEdge
from src.workers.ingestion_worker import IngestionWorker

from src.interfaces.quarantine import (
    ISeriesExtractorPipeline,
    ISemanticClassifier,
    ISensorPhysicsValidator,
    IKnowledgeTransfer,
)

from src.pipeline.series_extractor_pipeline import SeriesExtractorPipeline
from src.services.semantic_classifier import SemanticClassifier
from src.physics.sensor_physical_validator import SensorPhysicalValidator
from src.services.knowledge_transfer_service import KnowledgeTransferService
from src.factories.agent_factory import AgentFactory
from src.linguist.spatial_reconciler import SpatialReconciler
from src.linguist.quarantine_decision_gate import QuarantineDecisionGate
from src.utils.logging_setup import get_logger

logger = get_logger("LinguistService")


class LinguistService(QObject):
    """
    The 'Neuro-Symbolic' Gatekeeper Service.
    
    Pure Orchestrator Architecture (SOLID Compliant):
    - [SRP] Exclusively coordinates the quarantine state machine workflow.
    - [OCP] Data parsing, semantic inference, physics validation, spatial reconciliation
            and knowledge transfer are delegated to injected strategy components.
    - [DIP] Relies on abstract interfaces and specialized gatekeeper helpers.
    """

    update_signal = pyqtSignal(str, str, float)

    def __init__(
        self,
        app_state: AppState,
        ingestion_worker: IngestionWorker,
        agent_factory: AgentFactory,
        series_extractor: Optional[ISeriesExtractorPipeline] = None,
        semantic_classifier: Optional[ISemanticClassifier] = None,
        physics_validator: Optional[ISensorPhysicsValidator] = None,
        knowledge_transfer: Optional[IKnowledgeTransfer] = None,
        spatial_reconciler: Optional[SpatialReconciler] = None,
        decision_gate: Optional[QuarantineDecisionGate] = None,
    ):
        super().__init__()
        self.app_state = app_state
        self.ingestion = ingestion_worker
        self.agent_factory = agent_factory

        self.series_extractor = series_extractor or SeriesExtractorPipeline()
        self.semantic_classifier = semantic_classifier or SemanticClassifier()
        self.physics_validator = physics_validator or SensorPhysicalValidator(
            semantic_classifier=self.semantic_classifier,
            app_state=self.app_state
        )
        self.knowledge_transfer = knowledge_transfer or KnowledgeTransferService()

        # Specialized SRP submodules (Flat src/linguist architecture)
        self.spatial_reconciler = spatial_reconciler or SpatialReconciler(self.app_state)
        self.decision_gate = decision_gate or QuarantineDecisionGate(self.app_state)

        # Backward compatibility properties
        self.SAMPLE_CHUNK_SIZE = self.decision_gate.sample_chunk_size
        self.MAX_ATTEMPTS = self.decision_gate.max_attempts
        self.GRAMMAR_LOSS_THRESHOLD = self.decision_gate.grammar_loss_threshold

    @property
    def learning_attempts(self) -> Dict[str, int]:
        return self.decision_gate.learning_attempts

    @learning_attempts.setter
    def learning_attempts(self, val: Dict[str, int]) -> None:
        self.decision_gate.learning_attempts = val

    @pyqtSlot()
    def run_check(self):
        """Scans quarantined sources and progresses their state machine."""
        pipeline = self.ingestion.get_pipeline()
        sources = self.app_state.get_all_data_sources()

        for source in sources:
            if source.status == SourceStatus.QUARANTINE:
                self._process_quarantine_source(source, pipeline)

    def _process_quarantine_source(self, source: DataSource, pipeline: Any):
        """Executes the quarantine lifecycle: Collect -> Classify -> Train -> Validate -> Transfer -> Promote."""
        required_samples = self.decision_gate.get_required_samples(source.id)
        if not pipeline.has_enough_data(source.id, required_samples):
            return

        data_chunk = pipeline.get_quarantine_data(source.id)
        data_np = self.series_extractor.extract(data_chunk)

        sem_type, unit, confidence = self.semantic_classifier.classify(source, data_np, data_chunk)
        current_attempt = self.learning_attempts.get(source.id, 0)
        logger.info(
            f"🔬 [Linguist] {len(data_chunk)} amostras para '{source.name}' ({source.id}). "
            f"Modalidade: '{sem_type}' [{unit}]. Tentativa {current_attempt+1}..."
        )

        linguist = self.agent_factory.get_or_create_linguist(source.id)
        loss = linguist.train_step(data_np.tolist(), epochs=10, semantic_type=sem_type)

        target_threshold = self.decision_gate.get_grammar_threshold(sem_type)
        if loss < target_threshold:
            logger.info(
                f"🧠 [Linguist] Gramática aprendida (loss={loss:.4f} < teto={target_threshold:.4f}). Validando física..."
            )
            if self.physics_validator.validate(source, data_np, data_chunk, linguist):
                logger.info(f"⚖️ [Linguist] ✅ Consistência física APROVADA para '{source.name}'.")

                candidate_edges = self.spatial_reconciler.find_candidate_edges(
                    source,
                    agent_factory=self.agent_factory,
                    data_chunk=data_chunk,
                )
                if not candidate_edges:
                    scope_label = "local" if getattr(source, "is_local", True) else "global"
                    logger.warning(
                        f"❌ [Linguist] Sensor {scope_label} '{source.name}' ({source.id}) REJEITADO: "
                        f"Nenhuma aresta viária encontrada para vinculação na malha (Map Matching vazio ou sem coordenadas)."
                    )
                    self.decision_gate.reject_source(
                        source,
                        "Nenhuma aresta viária encontrada para vinculação na malha (Map Matching falhou ou inexistente). Descartado.",
                        self.agent_factory,
                        pipeline=pipeline
                    )
                    return

                orientation_data = self.spatial_reconciler.reconcile_orientation(
                    source=source,
                    candidate_edges=candidate_edges,
                    agent_factory=self.agent_factory,
                    data_chunk=data_chunk,
                    data_np=data_np,
                    sem_type=sem_type,
                )

                specialist = self.agent_factory.get_or_create_specialist(source.id)
                
                # Compile dedicated O(1) recipe with SI conversion for this sensor
                compiled_extractor = type(self.series_extractor)()
                compile_fn = getattr(compiled_extractor, "compile_recipe", None)
                if callable(compile_fn):
                    compile_fn(data_chunk, modality=sem_type, unit=unit, to_si=True)

                self.knowledge_transfer.transfer(
                    linguist,
                    specialist,
                    data_series=data_np,
                    extractor=compiled_extractor,
                    semantic_type=sem_type,
                    unit=unit,
                    orientation_data=orientation_data
                )

                # Validate if the unit is physically convertible to SI
                from src.physics.sensor_unit_converter import SensorUnitConverter
                rule_id = SensorUnitConverter.rule_for_unit(unit)
                if rule_id is None:
                    logger.warning(
                        f"❌ [Linguist] Sensor '{source.name}' ({source.id}) REJEITADO: "
                        f"Unidade '{unit}' fora do escopo de conversão para o SI. Descartado para evitar alucinação."
                    )
                    self.decision_gate.reject_source(
                        source,
                        f"Unidade de medida '{unit}' não conversível para o SI de tráfego. Descartado.",
                        self.agent_factory,
                        pipeline=pipeline
                    )
                    return

                # Persist conversion rule and extraction recipe in DataSource metadata
                if not isinstance(source.metadata, dict):
                    source.metadata = {}
                source.metadata["conversion_rule"] = rule_id
                recipe = getattr(compiled_extractor, "recipe", None)
                if isinstance(recipe, dict) and recipe:
                    source.metadata["extraction_path"] = recipe.get("field_path", [])
                    source.metadata["extraction_mode"] = recipe.get("mode", "fallback")

                self.decision_gate.promote_source(
                    source=source,
                    pipeline=pipeline,
                    data_np=data_np,
                    sem_type=sem_type,
                    unit=unit,
                    confidence=confidence,
                    agent_factory=self.agent_factory,
                    update_signal=self.update_signal,
                )
            else:
                self.decision_gate.reject_source(
                    source,
                    f"Violação das restrições físicas para a modalidade '{sem_type}'.",
                    self.agent_factory,
                    pipeline=pipeline
                )
        else:
            self.decision_gate.handle_learning_failure(
                source, pipeline, loss, self.agent_factory, semantic_type=sem_type
            )

    def _find_candidate_edges(self, source: DataSource) -> List[MapEdge]:
        return self.spatial_reconciler.find_candidate_edges(source)

    def _promote_source(self, *args, **kwargs):
        return self.decision_gate.promote_source(*args, **kwargs, update_signal=self.update_signal)

    def _reject_source(self, source: DataSource, reason: str):
        return self.decision_gate.reject_source(source, reason, self.agent_factory)
