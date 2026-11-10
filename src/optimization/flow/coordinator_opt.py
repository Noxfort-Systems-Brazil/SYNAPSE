# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import logging
from typing import Any
import torch
import numpy as np
import optuna

try:
    from torch_geometric.data import Data
    from torch_geometric.utils import degree
except ImportError:
    Data = None

from src.agents.coordinator_agent import CoordinatorAgent
from src.utils.convergence_tracker import MarginalConvergenceTracker

logger = logging.getLogger("Synapse.Strategies.Flow.Coordinator")


def optimize_coordinator(trial: optuna.Trial, graph_data: Any, device: torch.device) -> float:
    """Optimizes the Coordinator Agent (GATv2) purely on Topology (.net.xml)."""
    lr = trial.suggest_float("lr", 1e-5, 5e-4, log=True)
    hidden_channels = trial.suggest_categorical("hidden_channels", [32, 64, 128])
    heads = trial.suggest_categorical("heads", [2, 4, 8])
    dropout = trial.suggest_float("dropout", 0.1, 0.5)

    try:
        if Data is None:
            return float('inf')

        raw_edge_index = getattr(graph_data, "edge_index", None)
        if raw_edge_index is not None:
            edge_index = raw_edge_index
            if edge_index.dtype != torch.long:
                edge_index = edge_index.long()
        else:
            return float('inf')

        raw_x = getattr(graph_data, "x", None)
        if raw_x is not None:
            x = raw_x
            if x.dim() == 1:
                x = x.unsqueeze(1)
            num_nodes = x.shape[0]
            in_channels = x.shape[1]
        else:
            num_nodes = edge_index.max().item() + 1
            x = torch.ones((num_nodes, 1), dtype=torch.float32)
            in_channels = 1

        node_degrees = degree(edge_index[1], num_nodes=num_nodes, dtype=torch.float32)
        max_degree = node_degrees.max()
        if max_degree > 0:
            y = (node_degrees / max_degree).unsqueeze(1)
        else:
            y = torch.zeros((num_nodes, 1), dtype=torch.float32)

        clean_data = Data(x=x.float(), edge_index=edge_index, y=y).to(device)

        agent = CoordinatorAgent(
            in_channels=in_channels,
            hidden_channels=hidden_channels,
            out_channels=1,
            heads=heads,
            dropout=dropout,
            learning_rate=lr,
            device=device
        )
        agent.to(device)

        tracker = MarginalConvergenceTracker(
            min_epochs=5,
            max_epochs=25,
            patience=3,
            min_delta=1e-4,
            optuna_trial=trial
        )

        for epoch in range(tracker.max_epochs):
            loss = agent.train_step(clean_data)
            if not np.isfinite(loss):
                return float('inf')
            if tracker.step(epoch, loss, model=agent.model):
                break

        return tracker.best_loss

    except optuna.TrialPruned:
        raise
    except Exception as e:
        logger.warning(f"[Coordinator] Training failed: {e}")
        return float('inf')
    finally:
        if 'agent' in locals():
            del agent
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
