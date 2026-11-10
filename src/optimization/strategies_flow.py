# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import torch
import numpy as np
from typing import Any
import optuna

from src.optimization.flow.coordinator_opt import optimize_coordinator
from src.optimization.flow.fuser_opt import optimize_fuser
from src.optimization.flow.specialist_opt import optimize_specialist


class FlowStrategies:
    """
    Optimization Strategies for Flow-Control Agents (Coordinator, Fuser, Specialist).
    Delegates to dedicated optimization modules (SRP).
    """

    @staticmethod
    def coordinator_strategy(trial: optuna.Trial, graph_data: Any, device: torch.device) -> float:
        return optimize_coordinator(trial, graph_data, device)

    @staticmethod
    def fuser_strategy(trial: optuna.Trial, data: np.ndarray, device: torch.device) -> float:
        return optimize_fuser(trial, data, device)

    @staticmethod
    def specialist_strategy(trial: optuna.Trial, data: np.ndarray, device: torch.device) -> float:
        return optimize_specialist(trial, data, device)
