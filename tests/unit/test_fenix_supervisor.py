# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Fenix Process Supervisor Test Suite Aggregator (SOLID & Clean Architecture).
Delegates tests across modular suites under tests/unit/fenix/:
- test_recovery_policy.py: Sliding window and crash limiting tests.
- test_process_runner.py: Subprocess runner and async evolution coordinator tests.
"""

import time
import pytest
from unittest.mock import MagicMock, patch

from src.fenix.process_supervisor import (
    FenixProcessSupervisor,
    ProcessState,
    SupervisorConfig,
)
from src.fenix.protocols import (
    IProcessRunner,
    IRecoveryPolicy,
    IEvolutionCoordinator,
)

from tests.unit.fenix.test_recovery_policy import (
    test_recovery_policy_sliding_window_and_limits,
)
from tests.unit.fenix.test_process_runner import (
    test_subprocess_runner_spawn_and_lifecycle,
    test_evolution_coordinator_async_execution,
)


def test_supervisor_initial_state():
    """Verifies that supervisor starts in STOPPED state with no child process."""
    supervisor = FenixProcessSupervisor()
    assert supervisor.state == ProcessState.STOPPED
    assert supervisor.child_pid is None
    assert supervisor.is_child_alive() is False


def test_supervisor_start_and_stop_lifecycle():
    """Tests normal start and graceful stop lifecycle of the supervisor."""
    mock_runner = MagicMock(spec=IProcessRunner)
    mock_runner.pid = 99999
    mock_runner.is_alive = True
    mock_runner.spawn.return_value = True

    state_transitions = []
    supervisor = FenixProcessSupervisor(
        runner=mock_runner,
        on_status_changed=lambda state, msg: state_transitions.append(state),
    )

    success = supervisor.start()
    assert success is True
    assert supervisor.state == ProcessState.RUNNING
    assert supervisor.child_pid == 99999
    assert supervisor.is_child_alive() is True
    assert ProcessState.STARTING in state_transitions
    assert ProcessState.RUNNING in state_transitions

    supervisor.stop(timeout_seconds=0.1)
    assert supervisor.state == ProcessState.STOPPED
    mock_runner.terminate.assert_called_once()


def test_supervisor_auto_resurrection_on_crash():
    """Tests that supervisor detects child death and auto-resurrects the process."""
    mock_runner = MagicMock(spec=IProcessRunner)
    mock_runner.pid = 11111
    mock_runner.is_alive = True
    mock_runner.spawn.return_value = True
    mock_runner.poll.return_value = None

    config = SupervisorConfig(
        max_consecutive_crashes=3,
        restart_backoff_seconds=0.001,
        health_poll_interval_seconds=0.01,
    )

    status_changes = []
    supervisor = FenixProcessSupervisor(
        config=config,
        runner=mock_runner,
        on_status_changed=lambda st, msg: status_changes.append(st),
    )

    supervisor.start()
    assert supervisor.state == ProcessState.RUNNING

    # Simulate a crash handling tick
    supervisor._handle_child_crash(139)

    assert ProcessState.RESTARTING in status_changes
    assert supervisor.state == ProcessState.RUNNING
    assert mock_runner.spawn.call_count >= 2

    supervisor.stop()


def test_supervisor_exceed_crash_limit_halts():
    """Tests that supervisor halts and enters CRASHED state when max crash limit is exceeded."""
    config = SupervisorConfig(
        max_consecutive_crashes=2,
        crash_window_seconds=10.0,
        restart_backoff_seconds=0.001,
    )

    mock_runner = MagicMock(spec=IProcessRunner)
    mock_runner.pid = 33333
    mock_runner.is_alive = True
    mock_runner.spawn.return_value = True

    supervisor = FenixProcessSupervisor(config=config, runner=mock_runner)
    supervisor.start()

    # Crash 1 -> Restarts
    supervisor._handle_child_crash(1)
    assert supervisor.state == ProcessState.RUNNING

    # Crash 2 -> Restarts
    supervisor._handle_child_crash(1)
    assert supervisor.state == ProcessState.RUNNING

    # Crash 3 -> Exceeds limit (2) -> Enters CRASHED
    supervisor._handle_child_crash(1)
    assert supervisor.state == ProcessState.CRASHED

    supervisor.stop()


def test_supervisor_background_evolution():
    """Tests background Level 2 Evolution execution via supervisor."""
    mock_strategy = MagicMock()
    mock_strategy.name = "MockEvolution"
    mock_strategy.execute.return_value = True

    supervisor = FenixProcessSupervisor(evolution_strategy=mock_strategy)

    results = []
    success = supervisor.trigger_level2_evolution(
        on_complete=lambda ok, msg: results.append((ok, msg))
    )

    assert success is True
    time.sleep(0.1)

    assert len(results) == 1
    assert results[0][0] is True
    assert mock_strategy.execute.called


def test_supervisor_custom_injected_components():
    """Tests DIP & OCP: Inversion of Control via custom Runner, Recovery Policy, and Coordinator."""
    mock_runner = MagicMock(spec=IProcessRunner)
    mock_runner.pid = 77777
    mock_runner.is_alive = True
    mock_runner.spawn.return_value = True

    mock_policy = MagicMock(spec=IRecoveryPolicy)
    mock_policy.should_restart.return_value = True
    mock_policy.get_backoff_seconds.return_value = 0.001
    mock_policy.crash_count = 1

    mock_coordinator = MagicMock(spec=IEvolutionCoordinator)
    mock_coordinator.trigger_evolution.return_value = True

    supervisor = FenixProcessSupervisor(
        runner=mock_runner,
        recovery_policy=mock_policy,
        evolution_coordinator=mock_coordinator,
    )

    assert supervisor.start() is True
    assert supervisor.child_pid == 77777
    assert supervisor.is_child_alive() is True

    assert supervisor.trigger_level2_evolution() is True
    mock_coordinator.trigger_evolution.assert_called_once()

    supervisor._handle_child_crash(1)
    mock_policy.record_crash.assert_called_with(1)
    mock_policy.should_restart.assert_called()

    supervisor.stop()
    mock_runner.terminate.assert_called_once()
    mock_coordinator.stop.assert_called_once()
