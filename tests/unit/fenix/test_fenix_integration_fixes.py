# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import time
import pytest
from unittest.mock import MagicMock, patch

from src.fenix.process_supervisor import (
    FenixProcessSupervisor,
    ProcessState,
    SupervisorConfig,
)
from src.fenix.protocols import IProcessRunner
from src.services.fenix_service import FenixService
from src.engine.inference_engine import InferenceEngine


def test_supervisor_clean_exit_code_zero():
    """Verifies that child exit code 0 transitions to STOPPED without crash recording or restart."""
    mock_runner = MagicMock(spec=IProcessRunner)
    mock_runner.pid = 88888
    mock_runner.is_alive = True
    mock_runner.spawn.return_value = True

    # First poll running, second returns exit code 0
    poll_results = [None, 0]
    mock_runner.poll.side_effect = lambda: poll_results.pop(0) if poll_results else 0

    config = SupervisorConfig(health_poll_interval_seconds=0.01)
    supervisor = FenixProcessSupervisor(config=config, runner=mock_runner)

    supervisor.start()
    assert supervisor.state == ProcessState.RUNNING

    time.sleep(0.05)

    # Must transition cleanly to STOPPED, not CRASHED or RESTARTING
    assert supervisor.state == ProcessState.STOPPED
    assert supervisor.recovery_policy.crash_count == 0
    mock_runner.terminate.assert_called()


def test_supervisor_crashed_halts_supervision_loop():
    """Verifies that exceeding crash threshold halts loop and remains in CRASHED state."""
    config = SupervisorConfig(
        max_consecutive_crashes=1,
        crash_window_seconds=10.0,
        restart_backoff_seconds=0.001,
        health_poll_interval_seconds=0.01,
    )

    mock_runner = MagicMock(spec=IProcessRunner)
    mock_runner.pid = 99999
    mock_runner.is_alive = True
    mock_runner.spawn.return_value = True
    # Always returning crash code
    mock_runner.poll.return_value = 137

    supervisor = FenixProcessSupervisor(config=config, runner=mock_runner)
    supervisor.start()

    time.sleep(0.08)

    assert supervisor.state == ProcessState.CRASHED
    crashes_first = supervisor.recovery_policy.crash_count

    # Sleep longer to ensure loop does not keep piling crashes
    time.sleep(0.05)
    assert supervisor.recovery_policy.crash_count == crashes_first
    assert supervisor.state == ProcessState.CRASHED

    supervisor.stop()


def test_fenix_service_lifecycle_compatibility():
    """Verifies orchestrator compatibility aliases: start_watchdog, stop_watchdog, report_health."""
    service = FenixService()
    assert service.is_monitoring_active is False

    service.start_watchdog()
    assert service.is_monitoring_active is True

    # Test report_health forwarding
    with patch.object(service, "check_health_metrics") as mock_check:
        service.report_health({"alive": True, "loss": 0.45})
        mock_check.assert_called_once_with(0.45)

    service.stop_watchdog()
    assert service.is_monitoring_active is False


def test_inference_engine_reset_neural_state():
    """Verifies reset_neural_state resets node temporal history and auditor state."""
    mock_node = MagicMock()
    mock_node.reset_step_state = MagicMock()

    mock_graph = MagicMock()
    mock_graph.nodes = {"node_1": mock_node}

    mock_auditor = MagicMock()
    mock_auditor.reset_history = MagicMock()

    mock_processor = MagicMock()
    mock_processor.auditor = mock_auditor

    engine = InferenceEngine(
        app_state=MagicMock(),
        graph_manager=mock_graph,
        snapshot_builder=MagicMock(),
        processor=mock_processor,
        gating_policy=MagicMock(),
        forecast_imputer=MagicMock(),
    )

    engine.reset_neural_state()

    mock_node.reset_step_state.assert_called_once()
    mock_auditor.reset_history.assert_called_once()


def test_inference_engine_hot_swap_model(tmp_path):
    """Verifies hot_swap_model loads weights into fuser model safely."""
    import torch

    # Create dummy checkpoint
    dummy_path = tmp_path / "model.pth"
    torch.save({"model_state_dict": {"weight": torch.tensor([1.0, 2.0])}}, dummy_path)

    mock_fuser_model = MagicMock()
    mock_fuser = MagicMock()
    mock_fuser.model = mock_fuser_model

    mock_processor = MagicMock()
    mock_processor.fuser = mock_fuser

    engine = InferenceEngine(
        app_state=MagicMock(),
        graph_manager=MagicMock(),
        snapshot_builder=MagicMock(),
        processor=mock_processor,
        gating_policy=MagicMock(),
        forecast_imputer=MagicMock(),
    )

    success = engine.hot_swap_model(str(dummy_path))
    assert success is True
    mock_fuser_model.load_state_dict.assert_called_once()

    # Non-existent path returns False safely
    assert engine.hot_swap_model("non_existent_model.pth") is False
