# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Optional, Tuple, Any
from src.interfaces.node import INodeImputationStrategy, IPhysicsEngine
from src.strategies.kse_inertial_imputation import KseInertialImputationStrategy
from src.utils.logging_setup import logger


class HierarchicalImputationStrategy:
    """
    Implements cascading fallback imputation (SOLID SRP/OCP/DIP).
    
    Phases:
    1. Check Historical Golden DB (MEH Cascading / Hierarchical Match).
       - If non-zero historical data exists: Snap physics to truth and return historical value.
    2. Missing Data Gap / Data Hole / Zero Profile:
       - Delegates to KseInertialImputationStrategy (Last Known Good State + Kinematic Dead Reckoning).
    """

    def __init__(
        self,
        tolerance: float = 0.25,
        inertial_strategy: Optional[KseInertialImputationStrategy] = None
    ):
        self.tolerance = tolerance
        self.inertial_strategy = inertial_strategy or KseInertialImputationStrategy()

    def impute(
        self,
        source_id: str,
        timestamp: float,
        dt: float,
        physics_engine: IPhysicsEngine,
        historical_manager: Optional[Any] = None,
        fallback_steps: int = 0
    ) -> Tuple[float, str]:
        """
        Computes the imputed value and strategy description.
        Returns:
            (final_val: float, method_used: str)
        """
        historical_val = None

        # --- PHASE 1: CHECK GOLDEN DATABASE (MEH Cascading Resolution) ---
        if historical_manager is not None:
            hier_fn = getattr(historical_manager, "get_hierarchical_reading", None)
            if callable(hier_fn):
                historical_val = hier_fn(source_id, timestamp)
            exact_fn = getattr(historical_manager, "get_exact_reading", None)
            if historical_val is None and callable(exact_fn):
                historical_val = exact_fn(source_id, timestamp, tolerance=self.tolerance)

        # Only accept MEH reading if it contains real non-zero traffic profile
        if historical_val is not None and float(historical_val) > 0.1:
            # HIT! Recorded historical truth exists for this moment.
            physics_engine.predict(dt)
            physics_engine.update(float(historical_val))
            final_val = float(historical_val)
            method_used = "MEH (Hierarchical Match)"
        else:
            # MISS or ZERO profile -> PHASE 2: KSE INERTIAL DEAD RECKONING / PHYSICS PROJECTION
            physics_engine.predict(dt)
            kse_snapshot = physics_engine.get_kinetic_snapshot()
            snap_p = getattr(kse_snapshot, "p", None)
            raw_p = float(snap_p if snap_p is not None else 15.0)
            if snap_p is not None and raw_p > 0.0:
                final_val = raw_p
            else:
                final_val, _ = self.inertial_strategy.project_with_inertia(
                    source_id=source_id,
                    dt=dt,
                    physics_engine=physics_engine,
                    last_known_val=raw_p
                )
            method_used = "KSE (Physics Projection)"

        # Physical safety: Flow/Density cannot be negative
        final_val = max(0.0, final_val)

        if fallback_steps % 10 == 0:
            logger.info(f"[HierarchicalImputation] 🛡️ FALLBACK: {method_used} | Node={source_id} | Val: {final_val:.2f}")

        return final_val, method_used

