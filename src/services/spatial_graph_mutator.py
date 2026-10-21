# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Spatial Graph Mutator Service — Synthetic Data & Noise Augmentation.

Adheres to Single Responsibility Principle (SRP) by isolating synthetic noise
generation and mutation logic from optimization routines and model architectures.
"""

import random
import logging
from typing import List, Tuple
from src.domain.entities import MapEdge
from src.domain.model_contracts import ISpatialGraphMutator

logger = logging.getLogger("Synapse.Services.SpatialGraphMutator")


class SpatialGraphMutator(ISpatialGraphMutator):
    """
    Generates noisy mutant graphs from ground truth map edges for self-supervised alignment.
    """

    def mutate(
        self,
        edges: List[MapEdge],
        noise_scale: float = 20.0,
        drop_prob: float = 0.1,
    ) -> Tuple[List[MapEdge], List[int]]:
        """
        Creates a noisy mutant copy of edges: jitter + deletion + shuffle.

        Args:
            edges: List of source MapEdge entities.
            noise_scale: Standard deviation of Gaussian jitter applied to coordinates.
            drop_prob: Probability of dropping an edge to simulate missing sensor segments.

        Returns:
            Tuple of (mutant_edges, surviving_original_indices).
        """
        if not edges:
            return [], []

        indices = list(range(len(edges)))

        # 1. Probabilistic Deletion (Simulating missing road segments)
        surviving: List[int] = []
        for idx in indices:
            if random.random() > drop_prob or len(surviving) < min(3, len(edges)):
                surviving.append(idx)

        # 2. Shuffle (Simulating unordered incoming sensor detections)
        random.shuffle(surviving)

        # 3. Noisy Copies with Gaussian Jitter
        mutants: List[MapEdge] = []
        for orig_idx in surviving:
            e = edges[orig_idx]
            noisy_shape = [
                (px + random.gauss(0, noise_scale), py + random.gauss(0, noise_scale))
                for px, py in e.shape
            ]
            m = MapEdge(
                id=f"mut_{e.id}",
                from_node=e.from_node,
                to_node=e.to_node,
                shape=noisy_shape,
                weight=e.weight,
                signal_group_id=e.signal_group_id,
            )
            m._speed = getattr(e, '_speed', 13.89)
            m._num_lanes = getattr(e, '_num_lanes', 1)
            mutants.append(m)

        return mutants, surviving
