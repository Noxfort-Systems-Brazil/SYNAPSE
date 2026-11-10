# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
DeepONet Subnetwork Components: BranchNet and TrunkNet.
Encapsulates discrete sensor encoding and continuous coordinate basis representations (SRP).
"""

import torch
import torch.nn as nn


class BranchNet(nn.Module):
    """
    Branch Network for DeepONet.
    Encodes discrete sensor observations u = [v(x_1), v(x_2), ..., v(x_m)]
    into a p-dimensional latent coefficient space.
    """

    def __init__(
        self,
        in_features: int,
        p_latent: int = 64,
        hidden_dim: int = 128,
        num_layers: int = 3,
        dropout: float = 0.05
    ):
        super().__init__()
        layers = []
        curr_dim = in_features

        for i in range(num_layers - 1):
            layers.append(nn.Linear(curr_dim, hidden_dim))
            layers.append(nn.GELU())
            if dropout > 0.0:
                layers.append(nn.Dropout(dropout))
            curr_dim = hidden_dim

        layers.append(nn.Linear(curr_dim, p_latent))
        self.network = nn.Sequential(*layers)

    def forward(self, u: torch.Tensor) -> torch.Tensor:
        """
        Args:
            u: Sensor observations [Batch, in_features] or [Batch, in_features, SeqLen]
        Returns:
            b: Latent coefficients [Batch, p_latent]
        """
        if u.dim() == 3:
            u = u.flatten(start_dim=1)
        return self.network(u)


class TrunkNet(nn.Module):
    """
    Trunk Network for DeepONet.
    Encodes continuous spatiotemporal query coordinates y = (x, t)
    into p-dimensional continuous basis functions.
    """

    def __init__(
        self,
        coord_dim: int = 2,
        p_latent: int = 64,
        hidden_dim: int = 128,
        num_layers: int = 3
    ):
        super().__init__()
        layers = []
        curr_dim = coord_dim

        for i in range(num_layers - 1):
            layers.append(nn.Linear(curr_dim, hidden_dim))
            layers.append(nn.GELU())
            curr_dim = hidden_dim

        layers.append(nn.Linear(curr_dim, p_latent))
        self.network = nn.Sequential(*layers)

    def forward(self, y: torch.Tensor) -> torch.Tensor:
        """
        Args:
            y: Continuous coordinates [Batch, Num_Queries, coord_dim] or [Num_Queries, coord_dim]
        Returns:
            t: Basis evaluations [Batch, Num_Queries, p_latent] or [Num_Queries, p_latent]
        """
        return self.network(y)


__all__ = [
    "BranchNet",
    "TrunkNet",
]
