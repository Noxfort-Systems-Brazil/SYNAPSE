# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import time
from typing import Dict, Any, Optional

from src.interfaces.memory import ITemporalMemory
from src.interfaces.node import (
    IPhysicsEngine,
    INodeImputationStrategy,
    INodeGhostProcessor,
    INodeSnapshotFormatter
)
from src.node.node_state import NodeState


class NodeGhostProcessor:
    """
    Executes synthetic data fallback and missing data imputation when a sensor drops out.
    Stages:
    1. Historical readiness gate check
    2. Hierarchical / Physical value imputation via strategy
    3. Memory ingestion of synthetic reading and fallback counter tracking
    4. Continuous latent neural embedding refresh
    5. Formatted synthetic telemetry generation
    """

    def __init__(
        self,
        memory: ITemporalMemory,
        agent: Any,
        physics_engine: Optional[IPhysicsEngine],
        imputation_strategy: INodeImputationStrategy,
        snapshot_formatter: INodeSnapshotFormatter,
        historical_manager: Optional[Any] = None
    ):
        self._memory = memory
        self._agent = agent
        self._physics_engine = physics_engine
        self._imputation_strategy = imputation_strategy
        self._snapshot_formatter = snapshot_formatter
        self._historical_manager = historical_manager

    def process(self, state: NodeState) -> Dict[str, Any]:
        """Coordinates missing data imputation during sensor dropouts."""
        now = time.time()
        dt = now - state.last_timestamp
        if dt > 10.0 or dt <= 0.0:
            dt = 0.1
        state.last_timestamp = now

        # Impute missing value via Strategy (MEH Cascading Match vs. KSE Physics Projection)
        final_val, method_used = self._imputation_strategy.impute(
            source_id=state.source_id,
            timestamp=now,
            dt=dt,
            physics_engine=self._physics_engine,
            historical_manager=self._historical_manager,
            fallback_steps=state.fallback_steps
        )

        state.last_value = final_val

        # Ingest synthetic reading into memory
        if self._memory is not None:
            self._memory.push([final_val])
        state.increment_fallback()

        # Keep neural embeddings fresh
        current_embedding = state.last_embedding
        predict_fn = getattr(self._agent, "predict", None)
        if self._memory is not None and callable(predict_fn):
            history_np = self._memory.get_numpy()
            pred_emb = predict_fn(history_np)
            if pred_emb is not None:
                current_embedding = pred_emb
                state.last_embedding = current_embedding

        return self._snapshot_formatter.format_ghost_report(
            source_id=state.source_id,
            method_used=method_used,
            value=final_val,
            embedding=current_embedding,
            fallback_steps=state.fallback_steps,
            physics_engine=self._physics_engine
        )
