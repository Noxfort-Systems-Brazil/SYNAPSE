# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from enum import Enum
import time
import logging
from typing import Dict, Any, List, Optional
import numpy as np

from src.agents.base_agent import BaseAgent
from src.domain.entities import MapEdge, DataSource
from src.interfaces.pipelines import ICompassPipeline
from src.pipeline.compass_pipeline import CompassPipeline
from src.pipeline.vector_orientation_calc import extract_fluid_vector, detect_multichannel

logger = logging.getLogger("Synapse.Agents.Compass")


class TelemetryMode(str, Enum):
    """Canonical classification of sensor telemetry formats for directional reconciliation."""
    ONE_WAY = "ONE_WAY"                  # Via de mão única: O(1) Fast-Path
    FLUID_VECTOR = "FLUID_VECTOR"        # Opção 1: Percepção Fluida / SVision / Vetores de Rastreamento
    MULTICHANNEL = "MULTICHANNEL"        # Opção 2: Mão Dupla Multicanal (Faixas / Tripwires)
    SCALAR_AMBIGUOUS = "SCALAR_AMBIGUOUS"# Opção 3: Série Escalar Agregada / Desambiguação com Guarda
    NO_CANDIDATES = "NO_CANDIDATES"


class CompassAgent(BaseAgent):
    """
    The Compass Agent ('A Bússola').
    
    Pure Orchestrator Architecture (SOLID Compliant):
    - [SRP] Single Responsibility: Reconciles sensor orientation and directional alignment in two-way streets.
    - [OCP] Structured around 3 canonical telemetry modes:
            1. FLUID_VECTOR (SVision / Tracking)
            2. MULTICHANNEL (Faixas / Tripwires)
            3. SCALAR_AMBIGUOUS (Escalar / Guarda Anti-Cara-ou-Coroa)
    - [DIP] Relies on ICompassPipeline protocol for neural and geometric disambiguation.
    - [LSP] Conforms to BaseAgent interface for unified device management and lifecycle.
    """

    def __init__(
        self,
        pipeline: Optional[ICompassPipeline] = None,
        model_name: Optional[str] = None,
        name: str = "CompassAgent",
        confidence_threshold: float = 0.65,
        margin_threshold: float = 0.15,
        **kwargs: Any
    ):
        if pipeline is None:
            pipeline = CompassPipeline(
                model_name=model_name,
                confidence_threshold=confidence_threshold,
                margin_threshold=margin_threshold,
            )

        model = getattr(pipeline, "transformer", None)
        super().__init__(model=model, name=name)

        self.pipeline: ICompassPipeline = pipeline
        logger.debug(
            f"🧭 [CompassAgent] Agente inicializado (nome='{name}', "
            f"pipeline={type(pipeline).__name__}, modelo={getattr(pipeline, 'model_name', 'default')})."
        )

    def classify_telemetry_mode(
        self,
        source: DataSource,
        candidate_edges: List[MapEdge],
        data_chunk: Optional[List[Any]]
    ) -> TelemetryMode:
        """Determines the operational telemetry format before pipeline execution."""
        if not candidate_edges:
            return TelemetryMode.NO_CANDIDATES
        if len(candidate_edges) == 1:
            return TelemetryMode.ONE_WAY
        if extract_fluid_vector(source, data_chunk) is not None:
            return TelemetryMode.FLUID_VECTOR
        if detect_multichannel(source, candidate_edges, data_chunk) is not None:
            return TelemetryMode.MULTICHANNEL
        return TelemetryMode.SCALAR_AMBIGUOUS

    def inference(self, input_data: Any) -> Dict[str, Any]:
        """
        Unified BaseAgent inference contract.
        Expects dict with 'source', 'candidate_edges', and optional 'data_chunk', 'data_np', 'semantic_type'.
        """
        if isinstance(input_data, dict):
            return self.orient_and_reconcile(
                source=input_data.get("source"),
                candidate_edges=input_data.get("candidate_edges", []),
                data_chunk=input_data.get("data_chunk"),
                data_np=input_data.get("data_np"),
                semantic_type=input_data.get("semantic_type")
            )
        logger.warning(
            f"⚠️ [CompassAgent] Entrada inválida recebida em inference(): esperava dict, recebeu {type(input_data).__name__}."
        )
        return {
            "orientation": "INDETERMINADO",
            "primary_edge_id": None,
            "confidence": 0.0,
            "method": "invalid_input",
            "telemetry_mode": TelemetryMode.NO_CANDIDATES.value,
        }

    def orient_and_reconcile(
        self,
        source: DataSource,
        candidate_edges: List[MapEdge],
        data_chunk: Optional[List[Any]] = None,
        data_np: Optional[np.ndarray] = None,
        semantic_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delegates directional reconciliation to the CompassPipeline with full traceability logging.
        """
        src_id = getattr(source, "id", "desconhecido") if source else "None"
        src_name = getattr(source, "name", "desconhecido") if source else "None"
        src_status = getattr(getattr(source, "status", None), "value", getattr(source, "status", "UNKNOWN"))
        sample_count = len(data_chunk) if data_chunk else 0
        candidate_ids = [getattr(e, "id", str(e)) for e in candidate_edges] if candidate_edges else []
        has_prior_orientation = bool(
            source and source.metadata and ("orientation" in source.metadata or "orientation_vector" in source.metadata)
        )

        # 1. Identify canonical operational mode
        mode = self.classify_telemetry_mode(source, candidate_edges, data_chunk)

        logger.info(
            f"🧭 [CompassAgent] 🔍 Reconciliação direcional solicitada para sensor '{src_name}' ({src_id}). "
            f"[Modo Operacional: {mode.value} | Status: {src_status} | Amostras Quarentena: {sample_count} | Modalidade: '{semantic_type}']. "
            f"Arestas candidatas ({len(candidate_edges)}): {candidate_ids}. "
            f"Metadados prévios: {source.metadata if has_prior_orientation else 'Nenhum'}."
        )

        if not candidate_edges:
            logger.warning(
                f"⚠️ [CompassAgent] Nenhuma aresta candidata fornecida para '{src_name}' ({src_id}). "
                f"Reconciliação não pôde determinar o sentido da via."
            )

        t0 = time.perf_counter()
        orient_fn = getattr(self.pipeline, "orient_and_reconcile", None)
        if callable(orient_fn):
            result = orient_fn(
                source=source,
                candidate_edges=candidate_edges,
                data_chunk=data_chunk,
                data_np=data_np,
                semantic_type=semantic_type
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            result["telemetry_mode"] = mode.value

            method = result.get("method", "unknown")
            if method == "ambiguous_coin_flip_guard":
                logger.warning(
                    f"🧭 [CompassAgent] ⛔ Decisão 'Cara ou Coroa' BLOQUEADA para '{src_name}' ({src_id}) em {elapsed_ms:.1f}ms: "
                    f"Confiança={result.get('confidence', 0.0):.2%} insuficiente. Pista não invertida."
                )
            else:
                logger.info(
                    f"🧭 [CompassAgent] 🎯 Reconciliação concluída para '{src_name}' ({src_id}) em {elapsed_ms:.1f}ms: "
                    f"Modo={mode.value}, Sentido='{result.get('orientation')}', Aresta Primária='{result.get('primary_edge_id')}', "
                    f"Confiança={result.get('confidence', 0.0):.2%}, Método='{method}'."
                )
            return result

        logger.error(
            f"❌ [CompassAgent] Falha crítica: pipeline {type(self.pipeline).__name__} não possui método 'orient_and_reconcile'."
        )
        return {
            "orientation": "INDETERMINADO",
            "primary_edge_id": None,
            "confidence": 0.0,
            "method": "pipeline_missing",
            "telemetry_mode": mode.value,
        }

