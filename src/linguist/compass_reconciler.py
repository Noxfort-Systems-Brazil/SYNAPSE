# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import logging
from typing import List, Optional, Any, Dict
import numpy as np
from src.domain.entities import DataSource, MapEdge

logger = logging.getLogger("Synapse.Linguist.CompassReconciler")


class CompassReconciler:
    """
    Sub-component responsible for directional orientation reconciliation via CompassAgent.

    SOLID Compliance:
    - [SRP] Exclusively responsible for coordinating CompassAgent, resolving primary/secondary
            edges, and persisting edge associations into AppState.
    """

    def __init__(self, app_state: Any):
        self.app_state = app_state

    def reconcile(
        self,
        source: DataSource,
        candidate_edges: List[MapEdge],
        agent_factory: Any,
        data_chunk: Optional[List[Any]],
        data_np: np.ndarray,
        sem_type: str,
    ) -> Optional[Dict[str, Any]]:
        """Invokes CompassAgent to determine orientation and associates sensor to edge in AppState."""
        if not candidate_edges:
            return None

        orientation_data = None
        try:
            compass = agent_factory.get_or_create_compass(source.id)
            orientation_data = compass.orient_and_reconcile(
                source=source,
                candidate_edges=candidate_edges,
                data_chunk=data_chunk,
                data_np=data_np,
                semantic_type=sem_type,
            )
            primary_edge = (
                (orientation_data.get("primary_edge_id") if orientation_data else None)
                or (source.metadata.get("matched_edge_id") if source.metadata else None)
            )
            # If not in metadata, check if already associated in app_state
            if not primary_edge and self.app_state is not None:
                raw_edge = self.app_state.get_element_for_source(source.id)
                if not isinstance(raw_edge, str) and self.app_state.sources is not None:
                    raw_edge = self.app_state.sources.get_element_for_source(source.id)
                if isinstance(raw_edge, str) and raw_edge:
                    primary_edge = raw_edge

            # Fallback to candidate edge if available
            if not primary_edge and candidate_edges:
                primary_edge = candidate_edges[0].id

            is_indeterminate = orientation_data and orientation_data.get("orientation") in ("INDETERMINADO", "AMBIGUO")
            is_local = bool(source.is_local)

            if primary_edge:
                if is_local and self.app_state is not None:
                    if self.app_state.sources is not None:
                        self.app_state.sources.associate(source.id, primary_edge)
                        sec_edge = orientation_data.get("secondary_edge_id") if orientation_data else None
                        if sec_edge and not is_indeterminate:
                            self.app_state.sources.associate(source.id, sec_edge)
                    else:
                        self.app_state.associate(source.id, primary_edge)

                if orientation_data is not None and not orientation_data.get("primary_edge_id"):
                    orientation_data["primary_edge_id"] = primary_edge

                if is_indeterminate:
                    logger.info(
                        f"🧭 [CompassReconciler] Sensor '{source.name}' mantido na via "
                        f"'{primary_edge}' com orientação '{orientation_data.get('orientation')}'. Prevenindo inversão da malha."
                    )
                else:
                    scope_desc = "Local" if is_local else "Global"
                    logger.info(
                        f"🧭 [CompassReconciler] Sensor {scope_desc} '{source.name}' orientado para "
                        f"'{primary_edge}' ({orientation_data.get('orientation') if orientation_data else 'DEFAULT'})."
                    )
            else:
                logger.warning(
                    f"🧭 [CompassReconciler] Sensor '{source.name}' NÃO associado: "
                    f"Nenhuma via disponível para associação."
                )

            if source.metadata is not None and orientation_data:
                source.metadata["orientation"] = orientation_data.get("orientation")
                source.metadata["orientation_vector"] = orientation_data.get("vector")
        except Exception as e:
            logger.warning(f"⚠️ [CompassReconciler] Falha na reconciliação direcional: {e}")
        finally:
            if agent_factory is not None:
                agent_factory.release_compass(source.id)

        return orientation_data

