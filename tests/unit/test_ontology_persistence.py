# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
from unittest.mock import MagicMock
import pytest
import torch

from src.infrastructure.safetensors_repository import SafetensorsRepository
from src.models.modernbert import ModernBertSemanticExtractor
from src.linguist.quarantine_decision_gate import QuarantineDecisionGate
from src.domain.entities import DataSource, SourceStatus, SourceType


def test_safetensors_repository_save_and_load(tmp_path):
    repo = SafetensorsRepository()
    target_file = str(tmp_path / "test_ontology.safetensors")

    dummy_tensors = {
        "concept_a": torch.randn(1, 64),
        "concept_b": torch.randn(1, 64),
    }

    saved = repo.save_tensors(dummy_tensors, target_file)
    assert saved is True
    assert os.path.exists(target_file)

    loaded = repo.load_tensors(target_file)
    assert "concept_a" in loaded
    assert "concept_b" in loaded
    assert loaded["concept_a"].shape == (1, 64)


def test_quarantine_decision_gate_fast_path(tmp_path):
    repo = SafetensorsRepository()
    target_file = str(tmp_path / "ontology.safetensors")

    dummy_tensors = {
        "modality_vehicle_count": torch.randn(1, 64),
        "sensor_cam_01": torch.randn(1, 64),
    }
    repo.save_tensors(dummy_tensors, target_file)

    app_state = MagicMock()
    gate = QuarantineDecisionGate(app_state, ontology_path=target_file)
    assert len(gate.ontology_tensors) == 2

    # Known sensor in ontology
    known_src = DataSource(
        id="cam_01",
        name="Camera 01",
        source_type=SourceType.API,
        status=SourceStatus.QUARANTINE,
        semantic_type="Vehicle Count",
        inferred_unit="vehicles",
        confidence_score=0.95
    )
    assert gate.is_fast_path_eligible(known_src) is True
    assert gate.get_required_samples(known_src) == 1

    # Unknown sensor
    unknown_src = DataSource(
        id="radar_unknown",
        name="Radar Unknown",
        source_type=SourceType.API,
        status=SourceStatus.QUARANTINE,
        semantic_type=None
    )
    assert gate.is_fast_path_eligible(unknown_src) is False
    assert gate.get_required_samples(unknown_src) == 5
