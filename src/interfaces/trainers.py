# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Any, Dict, Protocol, runtime_checkable
from src.interfaces.base import IStepTrainable, IDeviceMovable, ITrainable


@runtime_checkable
class IFuserTrainer(IStepTrainable, IDeviceMovable, Protocol):
    """Contract for Fuser neural optimization and training routines."""
    def train(self, inputs: Any, targets: Any, epochs: int = 100, batch_size: int = 16, **kwargs: Any) -> float: ...


@runtime_checkable
class IAuditorTrainer(IStepTrainable, IDeviceMovable, Protocol):
    """Contract for Auditor neural optimization and adaptive threshold routines."""
    ...


@runtime_checkable
class IImputerTrainer(IStepTrainable, IDeviceMovable, Protocol):
    """Contract for Imputer masked training routines."""
    ...


@runtime_checkable
class ICorrectorTrainer(IStepTrainable, IDeviceMovable, Protocol):
    """Contract for Corrector PI-DVAE training and convergence routines."""
    def train(self, data: Any, epochs: int = 100, batch_size: int = 64, **kwargs: Any) -> Dict[str, list]: ...


@runtime_checkable
class ISpecialistTrainer(IStepTrainable, IDeviceMovable, Protocol):
    """Contract for Specialist training routines."""
    def train(self, inputs: Any, targets: Any, epochs: int = 1, batch_size: int = 32) -> float: ...


@runtime_checkable
class ILinguistTrainer(IStepTrainable, IDeviceMovable, Protocol):
    """Contract for NeuroSymbolic reasoning training routines."""
    def train_step(self, batch_data: Any, epochs: int = 10, semantic_type: Any = None) -> float: ...


@runtime_checkable
class ICoordinatorTrainer(IStepTrainable, IDeviceMovable, Protocol):
    """Contract for graph neural network optimization."""
    ...



