# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: src/pipeline/compass_pipeline.py
# Description: Pure Neural Pipeline Orchestrator for Directional Reconciliation (Clean Arch).

import os
import logging
from typing import Dict, Any, List, Optional, Tuple

import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel

# Enable Tensor Cores globally for matrix multiplications and cuDNN operations
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True

from src.domain.entities import MapEdge, DataSource
from src.interfaces.pipelines import ICompassPipeline
from src.utils.model_paths import get_modernbert_path
from src.pipeline.vector_orientation_calc import (
    compute_edge_vector,
    detect_multichannel,
    extract_fluid_vector,
    align_fluid_vector,
)
from src.pipeline.compass_disambiguator import CompassTwoWayDisambiguator

logger = logging.getLogger("Synapse.CompassPipeline")


class CompassPipeline(ICompassPipeline):
    """
    Dedicated Neural Pipeline Orchestrator for Directional Reconciliation.

    Coordinates:
    - Fast-path (O(1)) passthrough for single-direction streets (mão única).
    - Opção 1: Fluid vector kinematic alignment (SVision / YOLO trackings).
    - Opção 2: Multichannel dual-flow identification for simultaneous two-way sensors.
    - Opção 3: Scalar ambiguous flow with Anti-Cara-ou-Coroa Guard via CompassTwoWayDisambiguator.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[torch.device] = None,
        confidence_threshold: float = 0.65,
        margin_threshold: float = 0.15,
    ):
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.confidence_threshold = confidence_threshold
        self.margin_threshold = margin_threshold
        resolved_name = model_name or get_modernbert_path()
        self.model_name = resolved_name

        self.tokenizer = None
        self.transformer = None

        try:
            is_local = os.path.isdir(resolved_name)
            self.tokenizer = AutoTokenizer.from_pretrained(resolved_name, local_files_only=is_local)
            self.transformer = AutoModel.from_pretrained(resolved_name, local_files_only=is_local)
            self.transformer.to(self.device)
            self.transformer.eval()
            for p in self.transformer.parameters():
                p.requires_grad = False
            logger.info(f"[CompassPipeline] 🧭 ModernBERT inicializado com sucesso em {self.device}.")
        except Exception as e:
            logger.warning(f"[CompassPipeline] ⚠️ ModernBERT não disponível ({e}). Usando fallback heurístico.")

    def to(self, device: Any) -> 'CompassPipeline':
        self.device = torch.device(device) if isinstance(device, str) else device
        if self.transformer is not None:
            self.transformer.to(self.device)
        return self

    def _compute_edge_vector(self, edge: MapEdge) -> Tuple[float, float]:
        return compute_edge_vector(edge)

    def _detect_multichannel(
        self,
        source: DataSource,
        candidate_edges: List[MapEdge],
        data_chunk: Optional[List[Any]]
    ) -> Optional[Dict[str, Any]]:
        return detect_multichannel(source, candidate_edges, data_chunk)

    def orient_and_reconcile(
        self,
        source: DataSource,
        candidate_edges: List[MapEdge],
        data_chunk: Optional[List[Any]] = None,
        data_np: Optional[np.ndarray] = None,
        semantic_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Executes directional disambiguation for a sensor against candidate edges."""
        # --- GATE 0: No candidates ---
        if not candidate_edges:
            logger.warning(f"[CompassPipeline] ⚠️ Nenhuma aresta candidata informada para '{source.id}'.")
            return {
                "orientation": "INDETERMINADO",
                "primary_edge_id": None,
                "secondary_edge_id": None,
                "channels": {},
                "confidence": 0.0,
                "vector": (0.0, 0.0),
                "method": "no_candidates"
            }

        # --- GATE 1: Single-direction street (One-Way) -> O(1) Fast Path ---
        if len(candidate_edges) == 1:
            edge = candidate_edges[0]
            vec = self._compute_edge_vector(edge)
            logger.info(f"[CompassPipeline] ⚡ Via de mão única detectada para '{source.name}' -> {edge.id}.")
            return {
                "orientation": "IDA",
                "primary_edge_id": edge.id,
                "secondary_edge_id": None,
                "channels": {},
                "confidence": 1.0,
                "vector": vec,
                "method": "single_edge_fast"
            }

        # --- GATE 2 (Option 1): Fluid Vector / Kinematic Alignment (SVision / YOLO) ---
        fluid_vec = extract_fluid_vector(source, data_chunk)
        if fluid_vec is not None:
            aligned = align_fluid_vector(fluid_vec, candidate_edges)
            if aligned is not None:
                logger.info(
                    f"[CompassPipeline] 🌊 [Opção 1] Vetor de fluido/cinemática alinhado para '{source.name}' -> "
                    f"{aligned['primary_edge_id']} ({aligned['orientation']}, confiança={aligned['confidence']:.2%})."
                )
                return aligned

        # --- GATE 3 (Option 2): Multichannel / Dual-Direction Inspection (Lanes) ---
        multichannel_split = self._detect_multichannel(source, candidate_edges, data_chunk)
        if multichannel_split:
            logger.info(f"[CompassPipeline] 🔄 [Opção 2] Sensor multicanal de mão dupla detectado para '{source.name}'.")
            return multichannel_split

        # --- GATE 4 (Option 3): Scalar Ambiguous Flow (Anti-Coin-Flip Guard) ---
        return CompassTwoWayDisambiguator.disambiguate(
            source=source,
            candidate_edges=candidate_edges,
            data_chunk=data_chunk,
            data_np=data_np,
            transformer=self.transformer,
            tokenizer=self.tokenizer,
            device=self.device,
            compute_edge_vector_fn=self._compute_edge_vector,
            confidence_threshold=self.confidence_threshold,
            margin_threshold=self.margin_threshold,
        )
