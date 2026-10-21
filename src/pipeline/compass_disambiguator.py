# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: src/pipeline/compass_disambiguator.py
# Description: Two-way street Bayesian disambiguator and neural semantic scorer (SOLID: SRP).

import re
import math
import logging
from typing import Dict, Any, List, Optional, Tuple, Callable

import torch
import torch.nn.functional as F
import numpy as np
from torch.amp import autocast

from src.domain.entities import MapEdge, DataSource

logger = logging.getLogger("Synapse.CompassDisambiguator")


class CompassTwoWayDisambiguator:
    """Resolves directional choice between opposing edges using semantic clues, bearing, and NLP."""

    @classmethod
    def disambiguate(
        cls,
        source: DataSource,
        candidate_edges: List[MapEdge],
        data_chunk: Optional[List[Any]],
        data_np: Optional[np.ndarray],
        transformer: Optional[Any],
        tokenizer: Optional[Any],
        device: torch.device,
        compute_edge_vector_fn: Callable[[MapEdge], Tuple[float, float]],
        confidence_threshold: float = 0.65,
        margin_threshold: float = 0.15,
    ) -> Dict[str, Any]:
        edge_a = candidate_edges[0]
        edge_b = candidate_edges[1]

        vec_a = compute_edge_vector_fn(edge_a)
        vec_b = compute_edge_vector_fn(edge_b)

        # 1. Compile source text clues
        meta_str = " ".join([f"{k}:{v}" for k, v in (source.metadata or {}).items()])
        sample_str = ""
        if data_chunk and len(data_chunk) > 0:
            sample_str = str(data_chunk[:2])
        text_blob = f"{source.name} {source.connection_string} {meta_str} {sample_str}".lower()

        llr = 0.0

        # Evidence 1: Node & Edge Identifiers
        match_a = any(
            node_id and len(node_id) > 2 and node_id in text_blob
            for node_id in [edge_a.to_node.lower(), (edge_a.real_name or "").lower()]
        )
        match_b = any(
            node_id and len(node_id) > 2 and node_id in text_blob
            for node_id in [edge_b.to_node.lower(), (edge_b.real_name or "").lower()]
        )

        if match_a and not match_b:
            llr += 1.8
        elif match_b and not match_a:
            llr -= 1.8

        # Evidence 2: Cardinal & Directional Semantic Keywords
        words = set(re.findall(r"\b\w+\b", text_blob))
        sem_a = bool(words & {"centro", "inbound", "ida", "descida", "norte", "leste"})
        sem_b = bool(words & {"bairro", "outbound", "volta", "subida", "sul", "oeste"})
        if sem_a and not sem_b:
            llr += 1.2
        elif sem_b and not sem_a:
            llr -= 1.2

        # Evidence 2.5: Prior Configured Orientation in metadata
        if source.metadata and "orientation" in source.metadata:
            meta_ori = str(source.metadata["orientation"]).strip().upper()
            if meta_ori in ("IDA", "INBOUND", "CENTRO"):
                llr += 3.0
            elif meta_ori in ("VOLTA", "OUTBOUND", "BAIRRO"):
                llr -= 3.0

        # Evidence 3: Geometric Bearing Alignment (Metadata or Telemetry Chunk)
        bearing = None
        for key in ("bearing", "heading", "azimuth", "angle", "direction_deg"):
            if key in (source.metadata or {}):
                try:
                    bearing = float(source.metadata[key])
                    break
                except (ValueError, TypeError):
                    pass
        if bearing is None and data_chunk and len(data_chunk) > 0:
            sample0 = data_chunk[0]
            if isinstance(sample0, dict):
                for key in ("bearing", "heading", "azimuth", "angle", "direction_deg"):
                    if key in sample0:
                        try:
                            bearing = float(sample0[key])
                            break
                        except (ValueError, TypeError):
                            pass

        if bearing is not None:
            rad = math.radians(bearing)
            sensor_vec = (math.cos(rad), math.sin(rad))
            dot_a = sensor_vec[0] * vec_a[0] + sensor_vec[1] * vec_a[1]
            dot_b = sensor_vec[0] * vec_b[0] + sensor_vec[1] * vec_b[1]
            llr += 2.0 * (dot_a - dot_b)

        # Evidence 4: Neural Semantic Similarity (ModernBERT with noise suppression)
        if transformer is not None and tokenizer is not None:
            neural_score_a, neural_score_b = cls.compute_neural_semantic_scores(
                text_blob, edge_a, edge_b, transformer, tokenizer, device
            )
            sim_diff = neural_score_a - neural_score_b
            # Suppress microscopic noise (< 3%) caused by synthetic node IDs
            if abs(sim_diff) >= 0.03:
                llr += 2.0 * sim_diff

        # Posterior probability via Logistic Sigmoid
        prob_a = 1.0 / (1.0 + math.exp(-llr))
        prob_b = 1.0 - prob_a

        confidence = max(prob_a, prob_b)
        margin = abs(prob_a - prob_b)

        # Ambiguity / Anti-Coin-Flip Guard
        if confidence < confidence_threshold or margin < margin_threshold:
            logger.warning(
                f"[CompassDisambiguator] ⚠️ Decisão direcional inconclusiva para '{source.name}': "
                f"P(IDA)={prob_a:.2%}, P(VOLTA)={prob_b:.2%} (Margem={margin:.2%} < {margin_threshold:.2%}, "
                f"Confiança={confidence:.2%} < {confidence_threshold:.2%}). "
                f"Decisão 'cara ou coroa' bloqueada."
            )
            return {
                "orientation": "INDETERMINADO",
                "primary_edge_id": None,
                "secondary_edge_id": None,
                "channels": {},
                "confidence": float(confidence),
                "vector": (0.0, 0.0),
                "method": "ambiguous_coin_flip_guard",
                "probabilities": {"IDA": float(prob_a), "VOLTA": float(prob_b)},
                "margin": float(margin),
            }

        if prob_a > prob_b:
            chosen_edge = edge_a
            chosen_vec = vec_a
            orientation = "IDA"
        else:
            chosen_edge = edge_b
            chosen_vec = vec_b
            orientation = "VOLTA"

        logger.info(
            f"[CompassDisambiguator] 🧭 Desambiguação '{source.name}': "
            f"Edge {chosen_edge.id} ({orientation}) com confiança {confidence:.2%}. "
            f"LLR: {llr:.2f} (P(IDA)={prob_a:.2%}, P(VOLTA)={prob_b:.2%}, Margem={margin:.2%})."
        )

        return {
            "orientation": orientation,
            "primary_edge_id": chosen_edge.id,
            "secondary_edge_id": None,
            "channels": {},
            "confidence": float(confidence),
            "vector": chosen_vec,
            "method": "semantic_neural_reconciliation",
            "probabilities": {"IDA": float(prob_a), "VOLTA": float(prob_b)},
            "margin": float(margin)
        }

    @staticmethod
    def compute_neural_semantic_scores(
        text_blob: str,
        edge_a: MapEdge,
        edge_b: MapEdge,
        transformer: Any,
        tokenizer: Any,
        device: torch.device
    ) -> Tuple[float, float]:
        """Calculates contextual semantic similarity using ModernBERT embeddings."""
        try:
            desc_a = f"via de tráfego de {edge_a.from_node} para {edge_a.to_node} {edge_a.real_name or ''}"
            desc_b = f"via de tráfego de {edge_b.from_node} para {edge_b.to_node} {edge_b.real_name or ''}"

            texts = [text_blob[:128], desc_a, desc_b]
            inputs = tokenizer(texts, padding=True, truncation=True, max_length=64, return_tensors="pt")
            inputs = {k: v.to(device) for k, v in inputs.items()}

            device_type = device.type if device.type != 'mps' else 'cpu'
            with torch.no_grad():
                with autocast(device_type=device_type, enabled=(device.type == 'cuda')):
                    outputs = transformer(**inputs)
                attn_mask = inputs["attention_mask"].unsqueeze(-1)
                emb = (outputs.last_hidden_state.float() * attn_mask).sum(dim=1) / attn_mask.sum(dim=1).clamp(min=1e-6)
                emb = F.normalize(emb, p=2, dim=1)

            sim_a = F.cosine_similarity(emb[0:1], emb[1:2]).item()
            sim_b = F.cosine_similarity(emb[0:1], emb[2:3]).item()
            return float(sim_a), float(sim_b)
        except Exception as e:
            logger.debug(f"[CompassDisambiguator] NLP cosine similarity fallback: {e}")
            return 0.0, 0.0
