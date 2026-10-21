# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import time
import multiprocessing as mp
from ctypes import c_double, c_int
from typing import Dict, Any, Optional

from src.mlops.loss_engine import LossEngine
from src.mlops.drift_engine import DriftEngine
from src.mlops.mlops_pipe import MLOpsPipe


_SpawnProcess = mp.get_context("spawn").Process


class MLOpsProcess(_SpawnProcess):
    """
    Dedicated Out-of-Process Worker for MLOps Statistical Monitoring.
    
    Responsibilities:
    - Runs in a separate process, completely isolated from the GIL of the Neural Core.
    - Drains the unidirectional MLOpsPipe without blocking the real-time inference loop.
    - Computes continuous Reconstruction Loss and Population Stability Index (PSI) drift.
    - Exposes atomic shared memory metrics for instantaneous O(1) telemetry queries.
    """

    def __init__(
        self,
        pipe: MLOpsPipe,
        window_size: int = 1000,
        num_buckets: int = 20,
        tick_interval_s: float = 0.2
    ):
        super().__init__(name="SYNAPSE_MLOps_Process", daemon=True)
        self.pipe = pipe
        self.window_size = window_size
        self.num_buckets = num_buckets
        self.tick_interval_s = tick_interval_s

        ctx = mp.get_context("spawn")
        # Control event
        self._stop_event = ctx.Event()

        # Atomic shared state for O(1) reads
        self._shared_loss = ctx.Value(c_double, 0.008)
        self._shared_psi = ctx.Value(c_double, 0.012)
        self._shared_kl = ctx.Value(c_double, 0.0)
        self._shared_status = ctx.Value(c_int, 0)
        self._shared_samples = ctx.Value(c_int, 0)

    def run(self):
        """Main execution loop running in the dedicated MLOps process."""
        loss_engine = LossEngine()
        drift_engine = DriftEngine(
            window_size=self.window_size,
            num_buckets=self.num_buckets
        )

        accumulated_losses = []

        while not self._stop_event.is_set():
            snapshots = self.pipe.drain_snapshots(max_items=50)

            if snapshots:
                for s in snapshots:
                    # 1. Evaluate Loss if prediction and target are present
                    pred = s.get("prediction")
                    target = s.get("target")
                    if target is None:
                        target = s.get("history")
                    if pred is not None and target is not None:
                        loss_val = loss_engine.compute_reconstruction_loss(target, pred)
                        accumulated_losses.append(loss_val)

                    # 2. Ingest velocities/metrics into DriftEngine
                    vals = s.get("values")
                    if vals is None:
                        vals = s.get("velocities")
                    if vals is None:
                        vals = pred
                    if vals is not None:
                        drift_engine.add_samples(vals)

                # Update atomic loss
                if accumulated_losses:
                    recent_loss = float(sum(accumulated_losses[-20:]) / len(accumulated_losses[-20:]))
                    self._shared_loss.value = recent_loss
                    if len(accumulated_losses) > 500:
                        accumulated_losses = accumulated_losses[-100:]

                # Update atomic drift metrics
                metrics = drift_engine.compute_metrics()
                self._shared_psi.value = float(metrics["psi"])
                self._shared_kl.value = float(metrics["kl_div"])
                self._shared_status.value = int(metrics["status_code"])
                self._shared_samples.value = int(metrics["sample_count"])

            time.sleep(self.tick_interval_s)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Instantaneous O(1) non-blocking read of the latest MLOps metrics.
        Can be safely called by any thread or process without locks.
        """
        status_code = self._shared_status.value
        status_msg = "Stable" if status_code == 0 else ("Moderate Drift" if status_code == 1 else "Critical Drift")

        return {
            "loss": round(float(self._shared_loss.value), 6),
            "psi": round(float(self._shared_psi.value), 6),
            "kl_div": round(float(self._shared_kl.value), 6),
            "status_code": status_code,
            "status_message": status_msg,
            "sample_count": int(self._shared_samples.value)
        }

    def stop(self, timeout: float = 2.0):
        """Stops the MLOps process gracefully."""
        self._stop_event.set()
        self.join(timeout=timeout)
