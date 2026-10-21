# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import time
import numpy as np
import pytest
from unittest.mock import MagicMock

from src.mlops.mlops_pipe import MLOpsPipe, create_mlops_pipe, push_mlops_snapshot, drain_mlops_pipe
from src.mlops.mlops_process import MLOpsProcess
from src.agents.fuser_agent import FuserAgent
from src.interfaces.pipelines import IFusionPipeline
from src.interfaces.providers import ISensorCalibrator


def test_mlops_pipe_push_drain_and_saturation_drop():
    """Verifies that MLOpsPipe operates non-blocking and drops packets on OS buffer saturation."""
    pipe = create_mlops_pipe()

    # 1. Push 5 snapshots successfully
    for i in range(5):
        assert pipe.push_snapshot({"idx": i, "val": 10.0}) is True

    # 2. Drain snapshots
    drained = pipe.drain_snapshots(max_items=10)
    assert len(drained) == 5
    assert drained[0]["idx"] == 0
    assert drained[4]["idx"] == 4

    # 3. Drain again should be empty
    assert len(pipe.drain_snapshots(max_items=10)) == 0

    # 4. Fill OS pipe buffer to trigger non-blocking drop without hanging
    drop_occurred = False
    for _ in range(300):
        if not pipe.push_snapshot({"large": "X" * 2048}):
            drop_occurred = True
            break

    assert drop_occurred is True, "Expected non-blocking drop when OS pipe buffer is saturated"

    pipe.close()


def test_mlops_process_lifecycle_and_shared_metrics():
    """Verifies MLOpsProcess lifecycle, snapshot consumption, and atomic metrics update."""
    pipe = create_mlops_pipe()
    process = MLOpsProcess(pipe=pipe, window_size=50, num_buckets=5, tick_interval_s=0.05)

    # Initial metrics before starting
    init_m = process.get_metrics()
    assert init_m["loss"] == 0.008
    assert init_m["psi"] == 0.012

    process.start()

    try:
        # Push 60 snapshots with simulated velocities and predictions
        np.random.seed(42)
        for _ in range(60):
            sample_vel = np.random.normal(loc=60.0, scale=4.0, size=5).astype(np.float32)
            pipe.push_snapshot({
                "prediction": sample_vel,
                "target": sample_vel + np.random.normal(0.0, 0.5, size=5).astype(np.float32),
                "values": sample_vel
            })

        # Wait for worker process to drain and tick
        time.sleep(0.4)

        updated_m = process.get_metrics()
        assert updated_m["sample_count"] > 0
        assert np.isfinite(updated_m["loss"])
        assert np.isfinite(updated_m["psi"])
        assert "status_message" in updated_m

    finally:
        process.stop(timeout=1.0)
        pipe.close()


def test_fuser_agent_pipe_integration():
    """Verifies that FuserAgent seamlessly pushes snapshots into MLOpsPipe and reads metrics."""
    pipe = create_mlops_pipe()

    mock_process = MagicMock()
    mock_process.get_metrics.return_value = {
        "loss": 0.0042,
        "psi": 0.0091,
        "status_code": 0
    }

    mock_pipeline = MagicMock(spec=IFusionPipeline)
    mock_pipeline.execute.return_value = np.array([50.0, 52.0, 48.0], dtype=np.float32)

    mock_calibrator = MagicMock(spec=ISensorCalibrator)
    mock_calibrator.apply.side_effect = lambda raw_output, current_history, observability_mask: raw_output

    fuser = FuserAgent(
        pipeline=mock_pipeline,
        calibrator=mock_calibrator,
        num_variates=3,
        seq_len=10,
        mlops_pipe=pipe,
        mlops_process=mock_process
    )

    # Verify metrics delegate to process in O(1)
    metrics = fuser.get_mlops_metrics()
    assert metrics["loss"] == 0.0042
    assert metrics["drift"] == 0.0091

    # Perform inference -> should push to pipe
    history = np.ones((10, 3), dtype=np.float32) * 50.0
    result = fuser.fuse_state(current_history=history)

    assert result is not None
    drained = pipe.drain_snapshots(max_items=5)
    assert len(drained) == 1
    assert "prediction" in drained[0]
    np.testing.assert_allclose(drained[0]["prediction"], np.array([50.0, 52.0, 48.0]))

    pipe.close()


def test_fuser_agent_pipe_torch_tensor_detachment():
    """Verifies that FuserAgent correctly detaches PyTorch tensors to CPU NumPy arrays before pushing to MLOpsPipe."""
    import torch
    pipe = create_mlops_pipe()

    mock_pipeline = MagicMock(spec=IFusionPipeline)
    mock_pipeline.execute.return_value = torch.tensor([50.0, 52.0, 48.0], dtype=torch.float32)

    mock_calibrator = MagicMock(spec=ISensorCalibrator)
    mock_calibrator.apply.side_effect = lambda raw_output, current_history, observability_mask: raw_output

    fuser = FuserAgent(
        pipeline=mock_pipeline,
        calibrator=mock_calibrator,
        num_variates=3,
        seq_len=10,
        mlops_pipe=pipe
    )

    # Input as torch Tensor (like x_temporal from PINN / TCN)
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    history = torch.ones((10, 3), dtype=torch.float32, device=device) * 45.0
    velocities = torch.tensor([44.0, 46.0, 45.0], dtype=torch.float32, device=device)

    # Execute fuse_state
    _ = fuser.fuse_state(
        current_history=history,
        global_velocities=velocities
    )

    # Drain snapshots from pipe and ensure they are CPU NumPy arrays
    drained = pipe.drain_snapshots(max_items=5)
    assert len(drained) == 1
    snap = drained[0]

    assert isinstance(snap["prediction"], np.ndarray)
    assert isinstance(snap["target"], np.ndarray)
    assert isinstance(snap["values"], np.ndarray)

    np.testing.assert_allclose(snap["prediction"], np.array([50.0, 52.0, 48.0]))
    np.testing.assert_allclose(snap["target"], np.array([45.0, 45.0, 45.0]))
    np.testing.assert_allclose(snap["values"], np.array([44.0, 46.0, 45.0]))

    pipe.close()
