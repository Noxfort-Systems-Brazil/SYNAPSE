# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import torch
import torch.nn as nn
import torch.optim as optim
from typing import Any, Optional
from torch.amp import autocast, GradScaler

from src.interfaces.trainers import ICoordinatorTrainer


class CoordinatorTrainer(ICoordinatorTrainer):
    """
    Dedicated Training Routine & Optimizer for SpatialGAT Graph Models.
    """

    def __init__(
        self,
        model: nn.Module,
        learning_rate: float = 0.001,
        device: Optional[torch.device] = None
    ):
        self.model = model
        self.learning_rate = learning_rate
        self.device = device or torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

        self.optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        self.scaler = GradScaler(device=self.device.type if self.device.type in ('cuda', 'cpu') else 'cpu', enabled=(self.device.type == 'cuda'))
        self.criterion = nn.MSELoss()

    def to(self, device: Any) -> 'CoordinatorTrainer':
        self.device = torch.device(device) if isinstance(device, str) else device
        self.model.to(self.device)
        self.scaler = GradScaler(device=self.device.type if self.device.type in ('cuda', 'cpu') else 'cpu', enabled=(self.device.type == 'cuda'))
        return self

    def train_step(self, batch_data: Any) -> float:
        """
        Training step for Graph Data.
        """
        self.model.train()

        if isinstance(batch_data, (tuple, list)):
            x, edge_index, y = batch_data
            x, edge_index, y = x.to(self.device), edge_index.to(self.device), y.to(self.device)
        else:
            raw_x = getattr(batch_data, "x", None)
            raw_edge_index = getattr(batch_data, "edge_index", None)
            if raw_x is None or raw_edge_index is None:
                return 0.0
            x = raw_x.to(self.device)
            edge_index = raw_edge_index.to(self.device)
            raw_y = getattr(batch_data, "y", None)
            y = raw_y.to(self.device) if raw_y is not None else x

        self.optimizer.zero_grad()

        with autocast(device_type=self.device.type, enabled=(self.device.type == 'cuda')):
            out = self.model(x, edge_index)
            if isinstance(out, tuple):
                out = out[0]
            loss = self.criterion(out, y)

        self.scaler.scale(loss).backward()
        self.scaler.step(self.optimizer)
        self.scaler.update()

        return loss.item()
