# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
import json
from pathlib import Path
from src.storage.traffic_snapshot_store import TrafficSnapshotStore


def _sample_sensors(speed_1: str = "20.0 km/h", speed_2: str = "30.0 km/h"):
    return [
        {
            "id": "DET-01",
            "junction": "Av. Paulista x Consolação",
            "measuredSpeed": speed_1,
            "measuredFlow": "1.200 veíc/h",
        },
        {
            "id": "DET-02",
            "junction": "Av. Paulista x Campinas",
            "measuredSpeed": speed_2,
            "measuredFlow": "1.200 veíc/h",
        },
    ]


def test_baseline_snapshot_when_file_absent(tmp_path: Path):
    snapshot_file = tmp_path / "test_snapshot.json"
    store = TrafficSnapshotStore(file_path=str(snapshot_file))

    assert store.load_previous_snapshot() is None

    sensors = _sample_sensors("20.0 km/h", "30.0 km/h")
    summary = {"totalFlowPerHour": 2400, "avgSpeedKmh": 25.0, "saturationDegree": 0.70}
    comp = store.compute_comparison(sensors, summary, "Fluido", None)

    assert comp["hasPrevious"] is False
    assert comp["isBaseline"] is True
    assert comp["deltaSpeed"] == 0.0
    assert comp["deltaFlow"] == 0
    assert comp["currentSpeed"] == 25.0
    assert comp["currentSensorsCount"] == 2
    assert "Linha de base" in comp["summaryText"]


def test_save_and_subsequent_comparison(tmp_path: Path):
    snapshot_file = tmp_path / "test_snapshot.json"
    store = TrafficSnapshotStore(file_path=str(snapshot_file))

    # 1. First run: baseline
    initial_sensors = _sample_sensors("20.0 km/h", "20.0 km/h")
    initial_summary = {"totalFlowPerHour": 2400, "avgSpeedKmh": 20.0, "saturationDegree": 0.70}
    payload = store.build_snapshot_payload(
        protocol="PROT-001",
        sensors=initial_sensors,
        network_summary=initial_summary,
        flow_regime="Fluido",
    )
    saved_path = store.save_current_snapshot(payload)
    assert Path(saved_path).exists()

    # 2. Second run: load previous and compare with faster traffic
    loaded_prev = store.load_previous_snapshot()
    assert loaded_prev is not None
    assert loaded_prev["protocol"] == "PROT-001"
    assert loaded_prev["meanSpeed"] == 20.0

    updated_sensors = _sample_sensors("30.0 km/h", "30.0 km/h")
    # Add a third sensor to test delta sensor count
    updated_sensors.append({
        "id": "DET-03",
        "junction": "Av. Paulista x Brigadeiro",
        "measuredSpeed": "30.0 km/h",
        "measuredFlow": "1.200 veíc/h",
    })
    updated_summary = {"totalFlowPerHour": 3600, "avgSpeedKmh": 30.0, "saturationDegree": 0.70}

    comp = store.compute_comparison(updated_sensors, updated_summary, "Fluido", loaded_prev)

    assert comp["hasPrevious"] is True
    assert comp["isBaseline"] is False
    assert comp["previousSpeed"] == 20.0
    assert comp["currentSpeed"] == 30.0
    assert comp["deltaSpeed"] == 10.0
    assert comp["percentChangeSpeed"] == 50.0
    assert comp["previousSensorsCount"] == 2
    assert comp["currentSensorsCount"] == 3
    assert comp["previousProtocol"] == "PROT-001"
    assert "Evolução temporal" in comp["summaryText"]
    assert "+10.0 km/h" in comp["summaryText"]


def test_corrupt_file_handling(tmp_path: Path):
    snapshot_file = tmp_path / "corrupt_snapshot.json"
    snapshot_file.write_text("{invalid_json: true", encoding="utf-8")

    store = TrafficSnapshotStore(file_path=str(snapshot_file))
    assert store.load_previous_snapshot() is None
