# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import torch
import numpy as np
import optuna

from src.agents.specialist_agent import SpecialistAgent
from src.utils.convergence_tracker import MarginalConvergenceTracker


def optimize_specialist(trial: optuna.Trial, data: np.ndarray, device: torch.device) -> float:
    """Optimizes the Specialist Agent (TCN)."""
    lr = trial.suggest_float("lr", 1e-4, 1e-3, log=True)
    kernel_size = trial.suggest_int("kernel_size", 2, 5)
    dropout = trial.suggest_float("dropout", 0.1, 0.4)

    input_dim = data.shape[1] if data.ndim > 1 else 1
    hidden_dim = trial.suggest_categorical("hidden_dim", [32, 64])
    num_channels = [hidden_dim, hidden_dim]

    try:
        agent = SpecialistAgent(
            input_dim=input_dim,
            output_dim=input_dim,
            num_channels=num_channels,
            kernel_size=kernel_size,
            dropout=dropout,
            learning_rate=lr
        )
        agent.to(device)
    except Exception:
        return float('inf')

    seq_len = 30
    if len(data) > seq_len + 1:
        x = torch.FloatTensor(data[-seq_len-1:-1]).unsqueeze(0).to(device)
        y = torch.FloatTensor(data[-seq_len:]).unsqueeze(0).to(device)
    else:
        return float('inf')

    try:
        tracker = MarginalConvergenceTracker(
            min_epochs=3,
            max_epochs=20,
            patience=3,
            min_delta=1e-4,
            optuna_trial=trial
        )

        for epoch in range(tracker.max_epochs):
            loss = agent.train_step((x, y))
            if not np.isfinite(loss):
                return float('inf')
            if tracker.step(epoch, loss, model=agent.model):
                break

        return tracker.best_loss
    except optuna.TrialPruned:
        raise
    except Exception:
        return float('inf')
    finally:
        if 'agent' in locals():
            del agent
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
