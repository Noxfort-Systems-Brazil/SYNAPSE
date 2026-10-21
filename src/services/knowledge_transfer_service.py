# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Any, Optional, Dict
import numpy as np
import logging
from src.interfaces.quarantine import IKnowledgeTransfer

logger = logging.getLogger("Synapse.Services.KnowledgeTransferService")


class KnowledgeTransferService(IKnowledgeTransfer):
    """
    Encapsulates MLOps neural representation, weight transfer, and TCN teaching/warmup
    between the LinguistAgent (Learner) and the SpecialistAgent (Tactical Real-Time Converter).
    """

    def transfer(
        self,
        source_agent: Any,
        target_agent: Any,
        data_series: Optional[np.ndarray] = None,
        extractor: Optional[Any] = None,
        semantic_type: Optional[str] = None,
        unit: Optional[str] = None,
        orientation_data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> bool:
        """
        Transfers learned representations from source_agent and teaches/calibrates target_agent (TCN).
        
        Args:
            source_agent: Trained LinguistAgent containing the learned feature encoder.
            target_agent: SpecialistAgent whose TCN will convert real-time data for the graph.
            data_series: Optional extracted 1D time-series used to warmup and calibrate the TCN filters.
            extractor: Optional SeriesExtractorPipeline attached to the Specialist for autonomous parsing.
            semantic_type: Modality string ("Vehicle Count", "Vehicle Speed", etc.).
            unit: Engineering unit ("vehicles", "km/h", etc.).
            orientation_data: Optional directional decision dictionary produced by CompassAgent.
            
        Returns:
            bool: True if transfer and TCN initialization succeeded, False otherwise.
        """
        try:
            # 1. Weight Transfer (Encoder -> TCN)
            encoder_state = self._extract_encoder_state(source_agent)
            if encoder_state is not None:
                self._load_encoder_state(target_agent, encoder_state)
                logger.info("✅ [KnowledgeTransfer] Transferência de pesos neurais do Encoder para TCN realizada.")
            else:
                logger.info("ℹ️ [KnowledgeTransfer] Especialista inicializado com pesos nativos.")

            # 2. Attach Extractor & Modality to enable autonomous real-time conversion
            set_ext_fn = getattr(target_agent, "set_extractor", None)
            if callable(set_ext_fn) and extractor is not None:
                set_ext_fn(extractor, semantic_type=semantic_type, unit=unit)
                logger.info(f"🔗 [KnowledgeTransfer] Extrator autônomo e modalidade '{semantic_type}' [{unit}] vinculados à TCN Local.")

            # 2b. Attach Directional Orientation taught by the CompassAgent
            set_ori_fn = getattr(target_agent, "set_orientation", None)
            if callable(set_ori_fn) and orientation_data is not None:
                vec = orientation_data.get("vector")
                edge_id = orientation_data.get("primary_edge_id")
                channels = orientation_data.get("channels", {})
                ch_key = next(iter(channels.keys())) if channels else None
                set_ori_fn(vector=vec, edge_id=edge_id, channel_key=ch_key)
                logger.info(f"🧭 [KnowledgeTransfer] Orientação vetorial {vec} e aresta '{edge_id}' vinculadas ao Especialista.")

            # 3. TCN Warmup & Calibration (The "Teaching" Phase)
            if data_series is not None and len(data_series) > 0:
                self._warmup_specialist_tcn(target_agent, data_series)

            return True
        except Exception as e:
            logger.error(f"⚠️ [KnowledgeTransfer] Falha na transferência/calibração: {e}. O especialista continuará do zero.")
            return False

    def _warmup_specialist_tcn(self, target_agent: Any, data_series: np.ndarray):
        """Runs a forward prediction pass to calibrate TCN batch norms and embedding dimensions."""
        try:
            pred_fn = getattr(target_agent, "predict", None)
            if callable(pred_fn):
                embedding = pred_fn(data_series)
                logger.info(f"🎓 [KnowledgeTransfer] TCN calibrada com sucesso. Dimensão do embedding: {getattr(embedding, 'shape', len(embedding))}")
        except Exception as e:
            logger.debug(f"[KnowledgeTransfer] TCN warmup pass notice: {e}")

    def _extract_encoder_state(self, source_agent: Any) -> Optional[dict]:
        """Safely retrieves state_dict from source agent encoder."""
        model = getattr(source_agent, "model", None)
        if model is not None:
            ae = getattr(model, "ae", None)
            if ae is not None:
                encoder = getattr(ae, "encoder", None)
                enc_sd_fn = getattr(encoder, "state_dict", None) if encoder is not None else None
                if callable(enc_sd_fn):
                    return enc_sd_fn()
                ae_sd_fn = getattr(ae, "state_dict", None)
                if callable(ae_sd_fn):
                    return ae_sd_fn()
            model_sd_fn = getattr(model, "state_dict", None)
            if callable(model_sd_fn):
                return model_sd_fn()

        get_enc_fn = getattr(source_agent, "get_encoder_state_dict", None)
        if callable(get_enc_fn):
            return get_enc_fn()

        return None

    def _load_encoder_state(self, target_agent: Any, state_dict: dict):
        """Safely loads state_dict into target agent."""
        tcn = getattr(target_agent, "tcn", None)
        tcn_load_fn = getattr(tcn, "load_state_dict", None) if tcn is not None else None
        if callable(tcn_load_fn):
            tcn_load_fn(state_dict, strict=False)
            return

        load_enc_fn = getattr(target_agent, "load_encoder_state", None)
        if callable(load_enc_fn):
            load_enc_fn(state_dict)
            return

        model = getattr(target_agent, "model", None)
        model_load_fn = getattr(model, "load_state_dict", None) if model is not None else None
        if callable(model_load_fn):
            model_load_fn(state_dict, strict=False)

