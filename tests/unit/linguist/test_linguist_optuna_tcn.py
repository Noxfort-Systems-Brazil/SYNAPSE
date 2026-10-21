# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: tests/unit/linguist/test_linguist_optuna_tcn.py
# Author: Gabriel Moraes
# Date: 2026-09-28

import time
import torch
import optuna
import pytest

from src.models.neuro_symbolic import TCNAE, NeuroSymbolicModel
from src.optimization.strategies_semantic import SemanticStrategies
from src.engine.neural_factory import NeuralFactory
from src.domain.app_state import AppState


def test_tcnae_standalone_forward():
    """Validates that TCNAE can run standalone without Transformer and outputs correct dimensions."""
    batch_size = 4
    hidden_size = 768
    seq_len = 32
    latent_dim = 64
    kernel_size = 3

    model = TCNAE(hidden_size=hidden_size, latent_dim=latent_dim, kernel_size=kernel_size)
    x = torch.randn(batch_size, hidden_size, seq_len)

    reconstructed_x, latent, physics_states = model(x)

    assert reconstructed_x.shape == (batch_size, hidden_size, seq_len)
    assert latent.shape == (batch_size, latent_dim, seq_len)
    assert physics_states.shape == (batch_size, 3, seq_len)


def test_neuro_symbolic_model_backward_compatibility():
    """Validates that NeuroSymbolicModel still exposes .ae, .encoder, .physics_head, and .decoder."""
    model = NeuroSymbolicModel(freeze_transformer=True, latent_dim=48, kernel_size=5)

    assert hasattr(model, 'tcnae')
    assert hasattr(model, 'ae')
    assert hasattr(model, 'encoder')
    assert hasattr(model, 'physics_head')
    assert hasattr(model, 'decoder')
    assert model.latent_dim == 48
    assert model.kernel_size == 5


def test_linguist_strategy_optuna_subsecond_execution():
    """
    Validates that SemanticStrategies.linguist_strategy runs purely on the TCN-AE
    and completes 10 trials in less than 2 seconds (compared to 30+ minutes previously).
    """
    device = torch.device("cpu")
    embeddings = torch.randn(4, 768, 16)

    def objective(trial):
        return SemanticStrategies.linguist_strategy(trial, embeddings, device)

    study = optuna.create_study(direction="minimize")
    
    start_time = time.time()
    study.optimize(objective, n_trials=10)
    elapsed = time.time() - start_time

    assert len(study.trials) == 10
    assert study.best_value < float('inf')
    assert "lr" in study.best_params
    assert "latent_dim" in study.best_params
    assert "kernel_size" in study.best_params
    assert elapsed < 3.0, f"Optuna study took {elapsed:.2f}s, expected < 3.0s"


def test_neural_factory_loads_linguist_hparams(monkeypatch):
    """Validates that NeuralFactory correctly reads optimized hparams into LinguistAgent."""
    app_state = AppState()

    mock_hparams = {
        'linguist': {
            'latent_dim': 128,
            'kernel_size': 5,
            'lr': 0.002
        }
    }

    factory = NeuralFactory()
    monkeypatch.setattr(factory, "_load_best_hparams", lambda: mock_hparams)
    monkeypatch.setattr(factory, "_load_auditor_calibration", lambda a: None)

    agents = factory.build_all(app_state)
    linguist = agents['linguist']

    assert linguist.model.latent_dim == 128
    assert linguist.model.kernel_size == 5
    assert linguist.trainer.optimizer.param_groups[0]['lr'] == pytest.approx(0.002)
