# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
from src.fenix.recovery_policy import WindowedCrashRecoveryPolicy


def test_recovery_policy_sliding_window_and_limits():
    """Verifies that WindowedCrashRecoveryPolicy tracks crashes and enforces limit."""
    current_time = 1000.0
    time_provider = lambda: current_time

    policy = WindowedCrashRecoveryPolicy(
        max_consecutive_crashes=2,
        crash_window_seconds=60.0,
        restart_backoff_seconds=2.5,
        time_provider=time_provider,
    )

    assert policy.crash_count == 0
    assert policy.should_restart() is True
    assert policy.get_backoff_seconds() == 2.5

    # Crash 1
    policy.record_crash(1)
    assert policy.crash_count == 1
    assert policy.should_restart() is True

    # Crash 2
    policy.record_crash(1)
    assert policy.crash_count == 2
    assert policy.should_restart() is True

    # Crash 3 -> Exceeds max 2 crashes in window
    policy.record_crash(1)
    assert policy.crash_count == 3
    assert policy.should_restart() is False

    # Advance time beyond sliding window (60s)
    current_time = 1061.0
    assert policy.crash_count == 0
    assert policy.should_restart() is True

    # Reset
    policy.record_crash(1)
    assert policy.crash_count == 1
    policy.reset()
    assert policy.crash_count == 0
