# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
import torch
import numpy as np

# Base Protocols
from src.interfaces.base import IStepTrainable, IDeviceMovable, ITrainable

# Domain Trainer Protocols
from src.interfaces.trainers import (
    IAuditorTrainer,
    IImputerTrainer,
    ICorrectorTrainer,
    ISpecialistTrainer,
    ILinguistTrainer,
    ICoordinatorTrainer,
    IFuserTrainer
)

# Pipelines & Factories for cleanly wired components
from src.pipeline.auditor_pipeline import AuditorPipeline
from src.pipeline.imputer_pipeline import ImputerPipeline
from src.pipeline.corrector_pipeline import CorrectorPipeline
from src.pipeline.specialist_pipeline import SpecialistPipeline
from src.pipeline.coordinator_pipeline import CoordinatorPipeline
from src.factories.fuser_model_factory import FuserModelFactory

# Concrete Trainer Implementations
from src.trainer.auditor_trainer import AuditorTrainer
from src.trainer.imputer_trainer import ImputerTrainer
from src.trainer.corrector_trainer import CorrectorTrainer
from src.trainer.specialist_trainer import SpecialistTrainer
from src.trainer.coordinator_trainer import CoordinatorTrainer
from src.trainer.fuser_trainer import FuserTrainer


def test_base_protocol_hierarchy():
    """Verifies that ITrainable is backward-compatible with IStepTrainable."""
    assert ITrainable is IStepTrainable


def test_auditor_trainer_solid_protocols():
    """Verifies AuditorTrainer protocol compliance."""
    pipeline = AuditorPipeline(input_len=32, J=2, latent_dim=16)
    trainer = AuditorTrainer(model=pipeline.model, device=torch.device("cpu"))

    assert isinstance(trainer, IAuditorTrainer)
    assert isinstance(trainer, IStepTrainable)
    assert isinstance(trainer, IDeviceMovable)

    trainer.to("cpu")
    dummy_x = torch.randn(2, 32)
    loss = trainer.train_step(dummy_x)
    assert isinstance(loss, float)


def test_imputer_trainer_solid_protocols():
    """Verifies ImputerTrainer protocol compliance."""
    pipeline = ImputerPipeline(feature_dim=2, seq_len=16, patch_len=4, stride=2, d_model=32)
    trainer = ImputerTrainer(model=pipeline.model, device=torch.device("cpu"))

    assert isinstance(trainer, IImputerTrainer)
    assert isinstance(trainer, IStepTrainable)
    assert isinstance(trainer, IDeviceMovable)

    trainer.to("cpu")
    dummy_x = torch.randn(2, 16, 2)
    loss = trainer.train_step(dummy_x)
    assert isinstance(loss, float)


def test_corrector_trainer_solid_protocols():
    """Verifies CorrectorTrainer protocol compliance."""
    pipeline = CorrectorPipeline(input_dim=1, hidden_dim=16, latent_dim=8, kernel_size=3)
    trainer = CorrectorTrainer(model=pipeline.model, device=torch.device("cpu"))

    assert isinstance(trainer, ICorrectorTrainer)
    assert isinstance(trainer, IStepTrainable)
    assert isinstance(trainer, IDeviceMovable)

    trainer.to("cpu")
    dummy_x = torch.randn(4, 10)
    loss = trainer.train_step(dummy_x)
    assert isinstance(loss, float)


def test_specialist_trainer_solid_protocols():
    """Verifies SpecialistTrainer protocol compliance."""
    pipeline = SpecialistPipeline(input_dim=1, output_dim=16, num_channels=[8, 16])
    trainer = SpecialistTrainer(model=pipeline.model, input_dim=1, output_dim=16, device=torch.device("cpu"))

    assert isinstance(trainer, ISpecialistTrainer)
    assert isinstance(trainer, IStepTrainable)
    assert isinstance(trainer, IDeviceMovable)

    trainer.to("cpu")
    dummy_x = torch.randn(2, 20, 1)
    dummy_y = torch.randn(2, 16)
    loss = trainer.train_step((dummy_x, dummy_y))
    assert isinstance(loss, float)


def test_coordinator_trainer_solid_protocols():
    """Verifies CoordinatorTrainer protocol compliance."""
    pipeline = CoordinatorPipeline(in_channels=16, hidden_channels=16, out_channels=16)
    trainer = CoordinatorTrainer(model=pipeline.model, device=torch.device("cpu"))

    assert isinstance(trainer, ICoordinatorTrainer)
    assert isinstance(trainer, IStepTrainable)
    assert isinstance(trainer, IDeviceMovable)

    trainer.to("cpu")
    x = torch.randn(3, 16)
    edge_index = torch.tensor([[0, 1], [1, 2]], dtype=torch.long)
    loss = trainer.train_step((x, edge_index, x))
    assert isinstance(loss, float)


def test_fuser_trainer_solid_protocols():
    """Verifies FuserTrainer protocol compliance."""
    pipeline = FuserModelFactory.create_fusion_pipeline(
        num_variates=4,
        seq_len=10,
        pred_len=1,
        d_model=16,
        n_heads=2,
        layers=1,
        spatial_dim=8
    )
    trainer = FuserTrainer(composite_model=pipeline.module_dict, spatial_dim=8)

    assert isinstance(trainer, IFuserTrainer)
    assert isinstance(trainer, IStepTrainable)
    assert isinstance(trainer, IDeviceMovable)

    trainer.to("cpu")
    dummy_x = torch.randn(2, 10, 4)
    dummy_y = torch.randn(2, 1, 4)
    loss = trainer.train_step((dummy_x, dummy_y))
    assert isinstance(loss, float)
