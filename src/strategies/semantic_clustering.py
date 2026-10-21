# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import logging
from typing import Dict, List, Tuple, Optional
import torch
import torch.nn.functional as F


class CosineSemanticClusterer:
    """
    Clusterer that maps continuous sentence embeddings to discrete semantic concepts
    using dynamic cosine similarity matching and discovery.
    Decoupled from NLP neural feature extraction (SRP).
    """

    def __init__(self, similarity_threshold: float = 0.80, logger: Optional[logging.Logger] = None):
        self.similarity_threshold = similarity_threshold
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        
        self.learned_concepts: Dict[str, torch.Tensor] = {}
        self.concept_examples: Dict[str, List[str]] = {}
        self.concept_counter = 0

    def match_or_create_concept(
        self,
        current_embedding: torch.Tensor,
        clean_texts: List[str],
        device: torch.device = torch.device("cpu")
    ) -> Tuple[str, bool]:
        """
        Compares the current embedding against known concept centroids.
        If similarity >= threshold, updates existing concept.
        Otherwise, creates a new semantic concept.

        Returns:
            Tuple[concept_id, is_new_concept]
        """
        best_match_concept = None
        highest_similarity = -1.0

        for concept_id, concept_vector in self.learned_concepts.items():
            similarity = F.cosine_similarity(current_embedding, concept_vector.to(device)).item()
            if similarity > highest_similarity:
                highest_similarity = similarity
                best_match_concept = concept_id

        if highest_similarity >= self.similarity_threshold and best_match_concept is not None:
            self.logger.debug(f"Mapped to existing {best_match_concept} (Similarity: {highest_similarity:.2f})")
            new_examples = [ex for ex in clean_texts[:3] if ex not in self.concept_examples[best_match_concept]]
            self.concept_examples[best_match_concept].extend(new_examples)
            return best_match_concept, False

        # Create new concept
        self.concept_counter += 1
        new_concept_id = f"Semantic_Concept_{self.concept_counter}"
        
        # Store concept centroid on CPU to conserve GPU VRAM
        self.learned_concepts[new_concept_id] = current_embedding.cpu()
        self.concept_examples[new_concept_id] = clean_texts[:5]
        
        self.logger.info(f"Discovered new semantic pattern. Created: {new_concept_id}")
        return new_concept_id, True

    def get_ontology_report(self) -> Dict[str, List[str]]:
        """Returns the dictionary of dynamically learned concepts and their examples."""
        return self.concept_examples

    def get_concept_tensors(self) -> Dict[str, torch.Tensor]:
        """Returns the dictionary of concept centroid tensors."""
        return self.learned_concepts

    def load_concept_tensors(self, tensors: Dict[str, torch.Tensor]) -> None:
        """Restores concept centroid tensors from persistence."""
        self.learned_concepts = {k: v.cpu() for k, v in tensors.items()}
        self.concept_counter = len(self.learned_concepts)
