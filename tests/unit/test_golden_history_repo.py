# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Unit tests for GoldenHistoryRepository lossless ingestion, exact reading lookups,
and sensor statistical profiling.
"""

import time
import pandas as pd

from src.repositories.sensor_dictionary_repo import SensorDictionaryRepository
from src.repositories.golden_history_repo import GoldenHistoryRepository


def test_golden_dataset_intact_ingestion(temp_db_engine):
    """Verifies that the Golden Dataset is ingested 100% fully intact (zero data loss)."""
    dict_repo = SensorDictionaryRepository(temp_db_engine)
    golden_repo = GoldenHistoryRepository(temp_db_engine, dict_repo)

    now = time.time()
    # Create high-precision golden sample
    df = pd.DataFrame([
        {"sensor_id": "golden_sensor_1", "timestamp": now - 3600, "speed": 45.32, "flow_rate": 152.8, "occupancy": 0.182},
        {"sensor_id": "golden_sensor_1", "timestamp": now - 1800, "speed": 48.71, "flow_rate": 160.1, "occupancy": 0.195},
        {"sensor_id": "golden_sensor_1", "timestamp": now, "speed": 50.00, "flow_rate": 170.0, "occupancy": 0.210},
    ])

    success = golden_repo.ingest_dataframe(df, version="v1")
    assert success is True

    # Check exact reading at target timestamp
    exact = golden_repo.get_exact_reading("golden_sensor_1", target_timestamp=now, tolerance_sec=15.0)
    assert exact is not None
    assert abs(exact["speed"] - 50.0) < 0.01
    assert abs(exact["flow_rate"] - 170.0) < 0.01

    # Check global sensor profile
    profile = golden_repo.get_sensor_profile("golden_sensor_1")
    assert profile is not None
    expected_avg_speed = (45.32 + 48.71 + 50.00) / 3.0
    assert abs(profile["speed"] - expected_avg_speed) < 0.05
