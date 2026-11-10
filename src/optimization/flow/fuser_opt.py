# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import torch
import numpy as np
import optuna

from src.agents.fuser_agent import FuserAgent
from src.utils.convergence_tracker import MarginalConvergenceTracker


def optimize_fuser(trial: optuna.Trial, data: np.ndarray, device: torch.device) -> float:
    """Optimizes the Fuser Agent (iTransformer + PINN)."""
    lr = trial.suggest_float("lr", 1e-5, 1e-3, log=True)
    d_model = trial.suggest_categorical("d_model", [256, 512])
    layers = trial.suggest_int("layers", 1, 3)

    if data.ndim == 2:
        seq_len = 24
        if len(data) > seq_len:
            input_seq = data[-seq_len:]
            input_seq = torch.FloatTensor(input_seq).unsqueeze(0).to(device)
        else:
            return float('inf')
    else:
        return float('inf')

    num_variates = input_seq.shape[2]

    try:
        agent = FuserAgent(
            num_variates=num_variates,
            seq_len=24,
            d_model=d_model,
            layers=layers,
            learning_rate=lr
        )
        agent.to(device)
    except Exception:
        return float('inf')

    try:
        tracker = MarginalConvergenceTracker(
            min_epochs=3,
            max_epochs=20,
            patience=3,
            min_delta=1e-4,
            optuna_trial=trial
        )

        agent_model = getattr(agent, "model", None)
        if isinstance(agent_model, torch.nn.ModuleDict) and "itransformer" in agent_model:
            target_model = agent_model["itransformer"]
        else:
            target_model = getattr(agent, "itransformer", agent_model)

        for epoch in range(tracker.max_epochs):
            loss = agent.train_step((input_seq, input_seq))
            if not np.isfinite(loss):
                return float('inf')
            if tracker.step(epoch, loss, model=target_model):
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
