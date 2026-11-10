# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Spectral and Graph Convolutions Facade Module.
Re-exports Fourier (1D/2D) and Graph Laplacian Chebyshev blocks adhering to SOLID and Clean Architecture.
"""

from src.blocks.fourier_blocks import (
    SpectralConv1d,
    SpectralConv2d,
)
from src.blocks.chebyshev_blocks import (
    GraphLaplacianSpectralConv,
)

__all__ = [
    "SpectralConv1d",
    "SpectralConv2d",
    "GraphLaplacianSpectralConv",
]
