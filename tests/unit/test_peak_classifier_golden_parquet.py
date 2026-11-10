# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import json
import pytest
import pandas as pd
import numpy as np

from src.pipeline.peak_pipeline import ColumnDiscovery
from src.agents.peak_classifier_agent import PeakClassifierAgent


def test_column_discovery_golden_parquet_columns():
    """Verifies that ColumnDiscovery instantly matches Golden Parquet columns without ModernBERT."""
    golden_cols = [
        "event_timestamp", "sensor_id", "sumo_id", "location_text",
        "lat", "lon", "origin_type", "speed_val", "flow_val", "intensity_val"
    ]

    discovery = ColumnDiscovery()
    vol_col, spd_col = discovery.discover(golden_cols)

    assert vol_col == "flow_val"
    assert spd_col == "speed_val"


def test_column_discovery_alternative_traffic_columns():
    """Verifies that ColumnDiscovery gracefully handles custom Portuguese/legacy names."""
    custom_cols = ["timestamp", "id", "velocidade", "fluxo"]
    discovery = ColumnDiscovery()
    vol_col, spd_col = discovery.discover(custom_cols)

    assert vol_col == "fluxo"
    assert spd_col == "velocidade"


def test_peak_classifier_process_and_classify_golden_parquet(tmp_path):
    """End-to-end test of PeakClassifierAgent on synthetic Golden Parquet data without ModernBERT."""
    output_json = str(tmp_path / "peak_schedule_test.json")

    # Generate 168 hours of synthetic Golden Parquet data (1 canonical week)
    timestamps = pd.date_range("2026-03-02 00:00:00", periods=200, freq="h")
    df_golden = pd.DataFrame({
        "event_timestamp": timestamps,
        "sensor_id": "src_loop_01",
        "sumo_id": "edge_01",
        "location_text": "Av. Paulista",
        "lat": -23.56,
        "lon": -46.65,
        "origin_type": "inductive_loop",
        "speed_val": np.random.uniform(20.0, 60.0, size=len(timestamps)),
        "flow_val": np.random.uniform(100.0, 1500.0, size=len(timestamps)),
        "intensity_val": np.random.uniform(0.1, 0.9, size=len(timestamps))
    })

    itransformer_config = {
        'num_variates': 2,
        'd_model': 16,
        'n_heads': 2
    }
    timesnet_config = {
        'enc_in': 1,
        'd_model': 16,
        'd_ff': 32,
        'top_k': 2,
        'learning_rate': 1e-3
    }

    agent = PeakClassifierAgent(
        itransformer_config=itransformer_config,
        timesnet_config=timesnet_config,
        output_path=output_json
    )

    schedule = agent.process_and_classify(df_golden)

    assert os.path.exists(output_json)
    assert isinstance(schedule, dict)
    assert "Monday" in schedule
    assert "00:00" in schedule["Monday"]

    with open(output_json, "r") as f:
        saved_schedule = json.load(f)
    assert "Friday" in saved_schedule
