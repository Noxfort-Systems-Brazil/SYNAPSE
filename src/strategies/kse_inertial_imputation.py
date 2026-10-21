# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import numpy as np
from typing import Tuple, Optional
from src.interfaces.node import IPhysicsEngine
from src.utils.logging_setup import logger


class KseInertialImputationStrategy:
    """
    Single Responsibility: Kinematic Dead-Reckoning Imputation (SOLID SRP).
    
    Responsibilities:
    - Extrapolates missing or recovering sensor states using physics momentum.
    - Applies smooth asymptotic decay toward macroscopic road equilibrium.
    - Prevents sudden collapses to 0.0 or static flatlines during sensor gaps.
    """

    def __init__(self, baseline_density: float = 15.0, decay_rate: float = 0.05):
        self.baseline_density = baseline_density
        self.decay_rate = decay_rate

    def project_with_inertia(
        self,
        source_id: str,
        dt: float,
        physics_engine: IPhysicsEngine,
        last_known_val: Optional[float] = None
    ) -> Tuple[float, str]:
        """
        Executes dead reckoning on the physics engine with smooth asymptotic damping.
        
        Returns:
            (imputed_value: float, strategy_name: str)
        """
        clamped_dt = max(0.01, min(2.0, dt))
        physics_engine.predict(clamped_dt)

        kse_snapshot = physics_engine.get_kinetic_snapshot()
        raw_p = float(getattr(kse_snapshot, "p", self.baseline_density))
        raw_v = float(getattr(kse_snapshot, "v", 0.0))

        # Asymptotic decay toward baseline equilibrium over extended dead reckoning
        # target = baseline (15.0) or last known val
        target = float(last_known_val) if (last_known_val is not None and last_known_val > 0.0) else self.baseline_density
        damping = float(np.exp(-self.decay_rate * clamped_dt))
        
        imputed_val = (raw_p * damping) + (target * (1.0 - damping))
        
        # Physical boundary: traffic density/volume is non-negative and capped at jam density
        imputed_val = float(np.clip(imputed_val, 0.5, 125.0))

        phys_x = getattr(physics_engine, "x", None)
        if isinstance(phys_x, np.ndarray):
            try:
                phys_x[0, 0] = imputed_val
            except Exception:
                pass

        return imputed_val, "KSE (Inertial Dead Reckoning)"
