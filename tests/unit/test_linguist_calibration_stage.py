# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import json
import tempfile
import pytest
from unittest.mock import MagicMock
import numpy as np
import pandas as pd

from src.stages.linguist_calibration_stage import LinguistCalibrationStage
from src.linguist.quarantine_decision_gate import QuarantineDecisionGate
from src.domain.entities import DataSource, SourceType, SourceStatus


@pytest.fixture
def mock_golden_parquet():
    """Generates a temporary golden parquet file with minimal representative sensor data."""
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        path = f.name

    records = []
    # 20 samples per sensor
    for i in range(20):
        records.append({
            "event_timestamp": pd.Timestamp.now(),
            "sensor_id": "cam_01",
            "intensity_val": float(5 + (i % 3)),
            "flow_val": 10.0,
            "speed_val": 50.0
        })
        records.append({
            "event_timestamp": pd.Timestamp.now(),
            "sensor_id": "loop_01",
            "intensity_val": 0.0,
            "flow_val": float(800 + i * 10),
            "speed_val": 60.0
        })
        records.append({
            "event_timestamp": pd.Timestamp.now(),
            "sensor_id": "tomtom",
            "intensity_val": 0.0,
            "flow_val": 0.0,
            "speed_val": float(45.0 + (i % 5))
        })
        records.append({
            "event_timestamp": pd.Timestamp.now(),
            "sensor_id": "waze",
            "intensity_val": 0.0,
            "flow_val": float(750 + i * 5),
            "speed_val": 40.0
        })

    df = pd.DataFrame(records)
    df.to_parquet(path)
    yield path

    if os.path.exists(path):
        os.remove(path)


def test_linguist_calibration_stage_warm_start(tmp_path):
    """Verifies that an existing calibration file triggers warm start without re-running."""
    calib_file = tmp_path / "linguist_calibrated.json"
    calib_file.write_text(json.dumps({"default_grammar_threshold": 2.5}))

    stage = LinguistCalibrationStage(str(tmp_path))
    ctx = {
        "golden_path": str(tmp_path / "non_existent.parquet"),
        "linguist_checkpoint_path": str(calib_file),
    }

    assert stage.execute(ctx) is True


def test_linguist_calibration_stage_missing_golden(tmp_path):
    """Verifies graceful non-fatal exit when golden dataset is missing."""
    calib_file = tmp_path / "linguist_calibrated.json"
    stage = LinguistCalibrationStage(str(tmp_path))
    ctx = {
        "golden_path": str(tmp_path / "non_existent.parquet"),
        "linguist_checkpoint_path": str(calib_file),
    }

    assert stage.execute(ctx) is True
    assert not calib_file.exists()


def test_quarantine_decision_gate_loads_calibrated_thresholds(tmp_path):
    """Verifies QuarantineDecisionGate correctly parses and applies modality-specific thresholds."""
    calib_file = tmp_path / "linguist_calibrated.json"
    payload = {
        "default_grammar_threshold": 2.50,
        "modalities": {
            "Vehicle Count": 2.40,
            "Traffic Flow": 1.85,
            "Vehicle Speed": 1.50,
            "Traffic Density": 2.00
        }
    }
    calib_file.write_text(json.dumps(payload))

    gate = QuarantineDecisionGate(
        app_state=MagicMock(),
        calibration_path=str(calib_file)
    )

    assert gate.get_grammar_threshold("Vehicle Count") == 2.40
    assert gate.get_grammar_threshold("Traffic Flow") == 1.85
    assert gate.get_grammar_threshold("Vehicle Speed") == 1.50
    assert gate.get_grammar_threshold("Unknown Modality") == 2.50


def test_quarantine_decision_gate_approves_realistic_losses(tmp_path):
    """
    Verifies that realistic losses (1.70 to 1.80) that previously caused spurious
    rejections under rigid 0.5 are now accepted when calibrated thresholds are active.
    """
    calib_file = tmp_path / "linguist_calibrated.json"
    payload = {
        "default_grammar_threshold": 2.50,
        "modalities": {
            "Vehicle Count": 2.40,
            "Traffic Flow": 1.90,
            "Vehicle Speed": 1.50
        }
    }
    calib_file.write_text(json.dumps(payload))

    gate = QuarantineDecisionGate(
        app_state=MagicMock(),
        calibration_path=str(calib_file)
    )

    # Threshold for Vehicle Count is 2.40 -> loss 1.7082 is well under ceiling
    thresh_count = gate.get_grammar_threshold("Vehicle Count")
    assert 1.7082 < thresh_count

    # Threshold for Traffic Flow is 1.90 -> loss 1.7835 is well under ceiling
    thresh_flow = gate.get_grammar_threshold("Traffic Flow")
    assert 1.7835 < thresh_flow


def test_quarantine_decision_gate_rejects_abnormal_losses(tmp_path):
    """Verifies that truly corrupt or non-physical data (e.g. loss 9.5) is still rejected."""
    calib_file = tmp_path / "linguist_calibrated.json"
    payload = {
        "default_grammar_threshold": 2.50,
        "modalities": {
            "Vehicle Count": 2.40
        }
    }
    calib_file.write_text(json.dumps(payload))

    app_state = MagicMock()
    gate = QuarantineDecisionGate(
        app_state=app_state,
        max_attempts=2,
        calibration_path=str(calib_file)
    )

    source = DataSource(id="cam_bad", name="Bad Camera", source_type=SourceType.MQTT)
    pipeline = MagicMock()
    agent_factory = MagicMock()

    # Attempt 1: abnormal loss (9.50 >= 2.40) -> buffer extended
    gate.handle_learning_failure(source, pipeline, loss=9.50, agent_factory=agent_factory, semantic_type="Vehicle Count")
    pipeline.extend_quarantine_buffer.assert_called_once_with("cam_bad", 5)

    # Attempt 2: still abnormal -> rejected
    gate.handle_learning_failure(source, pipeline, loss=9.20, agent_factory=agent_factory, semantic_type="Vehicle Count")
    assert source.status == SourceStatus.REJECTED


def test_quarantine_decision_gate_resolves_path_scaffolder_and_env(tmp_path, monkeypatch):
    """Verifies QuarantineDecisionGate resolves linguist_calibrated.json via SYNAPSE_HOME / PathScaffolder."""
    config_dir = tmp_path / "data" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    calib_file = config_dir / "linguist_calibrated.json"
    calib_file.write_text(json.dumps({
        "default_grammar_threshold": 1.95,
        "modalities": {"Vehicle Speed": 1.42}
    }))

    monkeypatch.setenv("SYNAPSE_HOME", str(tmp_path))
    gate = QuarantineDecisionGate(app_state=MagicMock())
    assert gate.get_grammar_threshold("Vehicle Speed") == 1.42
    assert gate.get_grammar_threshold("Unknown") == 1.95

