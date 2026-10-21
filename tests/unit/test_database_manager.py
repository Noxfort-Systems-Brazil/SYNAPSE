# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Unit tests for DatabaseManager facade orchestration, operational sessions lifecycle,
and non-blocking async telemetry worker flushing.
"""

from src.database.database_manager import DatabaseManager


def test_database_manager_facade_and_async_worker(temp_db_engine):
    """Verifies DatabaseManager orchestrating the async worker and operational sessions."""
    db_mgr = DatabaseManager(engine=temp_db_engine, auto_start_worker=True)

    # Start session
    sid = db_mgr.start_operation_session()
    assert sid is not None

    # Push telemetry to async worker
    for _ in range(5):
        db_mgr.push_telemetry(
            sensor_id="sensor_async",
            speed=55.0,
            flow_rate=180.0,
            occupancy=0.22
        )

    # Stop worker gracefully, which flushes queued items deterministically without sleep
    db_mgr.stop()

    # End session
    ended = db_mgr.end_operation_session(status="FINALIZADO_NORMAL")
    assert ended is True

    # Verify telemetry was flushed to database
    history = db_mgr.query_telemetry_history()
    async_samples = [h for h in history if h["sensor_str_id"] == "sensor_async"]
    assert len(async_samples) >= 1
    assert sum(s["sample_count"] for s in async_samples) == 5
