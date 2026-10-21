# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class OptimizationTask:
    """
    Declarative description of a single Optuna optimization phase.
    
    The OptimizerService iterates over a list of these tasks without
    knowing anything about the concrete agents or strategies — adhering
    to the Dependency Inversion Principle (DIP).
    
    Attributes:
        name: Internal key used for checkpoint dict (e.g., 'coordinator').
        label: Human-readable label with emoji for logs/UI.
        objective_fn: Callable(trial) -> float. The Optuna objective.
        slope_threshold: Convergence slope for early stopping.
        window: Number of past trials for convergence regression.
        enabled: Toggle to skip a phase without modifying the orchestrator (OCP).
        post_hook: Optional callable to run after optimization (e.g., save diploma).
    """
    name: str
    label: str
    objective_fn: Callable
    slope_threshold: float = 1e-5
    window: int = 25
    enabled: bool = True
    post_hook: Optional[Callable] = field(default=None, repr=False)
