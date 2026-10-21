# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import time
import pytest
from unittest.mock import MagicMock, patch

from src.fenix.process_runner import SubprocessRunner
from src.fenix.evolution_coordinator import FenixEvolutionCoordinator


def test_subprocess_runner_spawn_and_lifecycle():
    """Verifies that SubprocessRunner manages child processes correctly."""
    mock_popen = MagicMock()
    mock_popen.pid = 44444
    mock_popen.poll.return_value = None

    runner = SubprocessRunner()
    assert runner.is_alive is False
    assert runner.pid is None
    assert runner.poll() is None

    with patch("subprocess.Popen", return_value=mock_popen):
        success = runner.spawn(["echo", "hello"])
        assert success is True
        assert runner.is_alive is True
        assert runner.pid == 44444
        assert runner.poll() is None

        runner.terminate(timeout_seconds=0.1)
        mock_popen.terminate.assert_called_once()
        assert runner.is_alive is False


def test_evolution_coordinator_async_execution():
    """Verifies that FenixEvolutionCoordinator executes background strategy."""
    mock_strategy = MagicMock()
    mock_strategy.name = "MockEvolution"
    mock_strategy.execute.return_value = True

    coordinator = FenixEvolutionCoordinator(strategy=mock_strategy)
    assert coordinator.is_evolving is False

    results = []
    success = coordinator.trigger_evolution(on_complete=lambda ok, msg: results.append((ok, msg)))
    assert success is True

    # Wait for thread
    time.sleep(0.1)

    assert len(results) == 1
    assert results[0][0] is True
    assert coordinator.is_evolving is False
    mock_strategy.execute.assert_called_once()
