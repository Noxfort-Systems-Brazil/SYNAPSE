# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Any, Protocol, runtime_checkable, Self


@runtime_checkable
class IDeviceMovable(Protocol):
    """Contract for models and pipelines that can be transferred across computing devices (CPU/GPU)."""
    def to(self, device: Any) -> Self:
        """Moves internal model/tensors to the specified computing device."""
        ...


@runtime_checkable
class IStepTrainable(Protocol):
    """Atomic contract for neural optimization step given a batch of data."""
    def train_step(self, batch_data: Any, **kwargs: Any) -> float:
        """Executes a single optimization step given a batch of data."""
        ...


# Backward compatibility alias for IStepTrainable
ITrainable = IStepTrainable

