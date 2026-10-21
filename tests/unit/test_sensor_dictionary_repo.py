# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Unit tests for SensorDictionaryRepository string-to-integer normalization and RAM caching.
"""

from src.repositories.sensor_dictionary_repo import SensorDictionaryRepository


def test_sensor_dictionary_caching(temp_db_engine):
    """Verifies string to integer normalization and RAM caching."""
    repo = SensorDictionaryRepository(temp_db_engine)

    # First lookup should insert
    id1 = repo.get_or_create("sensor_loop_av_paulista_01")
    assert id1 > 0

    # Second lookup should hit RAM cache
    id2 = repo.get_or_create("sensor_loop_av_paulista_01")
    assert id1 == id2

    # Reverse lookup
    str_name = repo.get_str_id(id1)
    assert str_name == "sensor_loop_av_paulista_01"

    # Bulk lookup
    bulk = repo.bulk_get_or_create(["sensor_loop_av_paulista_01", "sensor_radar_reboucas_02"])
    assert len(bulk) == 2
    assert bulk["sensor_loop_av_paulista_01"] == id1
    assert bulk["sensor_radar_reboucas_02"] > 0
