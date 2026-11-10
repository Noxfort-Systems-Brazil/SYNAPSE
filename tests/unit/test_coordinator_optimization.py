# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import torch
import optuna
from unittest.mock import MagicMock
from torch_geometric.data import Data

from src.optimization.flow.coordinator_opt import optimize_coordinator


def test_optimize_coordinator_with_multidimensional_features():
    """
    Verifies that optimize_coordinator properly handles 2D spatial coordinates (shape [N, 2])
    without throwing matrix multiplication shape errors (mat1 and mat2 cannot be multiplied).
    """
    device = torch.device("cpu")
    num_nodes = 29
    num_edges = 76

    # 2D coordinates as emitted by SUMO graph loader
    x = torch.randn(num_nodes, 2, dtype=torch.float32)
    edge_index = torch.randint(0, num_nodes, (2, num_edges), dtype=torch.long)
    graph_data = Data(x=x, edge_index=edge_index)

    # Mock Optuna trial
    trial = MagicMock(spec=optuna.Trial)
    trial.suggest_float.side_effect = lambda name, low, high, **kwargs: 1e-4
    trial.suggest_categorical.side_effect = lambda name, choices: choices[0]
    trial.should_prune.return_value = False

    loss = optimize_coordinator(trial, graph_data, device)

    # Loss must be a finite positive number, not float('inf')
    assert loss != float("inf")
    assert isinstance(loss, float)
    assert loss > 0
