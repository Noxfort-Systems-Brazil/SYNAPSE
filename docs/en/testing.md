# 🧪 SYNAPSE: Testing & Quality Assurance Suite

This document outlines the testing architecture, pytest suites, synthetic telemetry generators, mock fixtures, and coverage validation guidelines for **SYNAPSE CORE**.

⬅️ [Documentation Hub](README.md) | 🛡️ [Safety & Watchdog](safety_and_watchdog.md) | 🏛️ [Core Architecture](architecture.md)

---

## 1. Test Architecture Overview

Testing in SYNAPSE is organized into distinct categories under the `tests/` directory:

- **Unit Tests (`tests/unit/`)**: Verify individual domain entities, mathematical operators, and state machine transitions in isolation.
- **Model Tests (`tests/models/`)**: Validate forward and backward passes, tensor shapes, gradient flow, and loss functions for all 11 MARKVART™ architectures.
- **Integration Tests (`tests/integration/`)**: Test end-to-end data flow from the Ingestion Hub through the AppState facade to the HFT gRPC streamer.
- **IPC Tests (`tests/ipc/`)**: Validate the Stdio newline JSON-RPC protocol against edge-case payloads, malformed JSON, and burst loads.
- **Benchmarks (`tests/benchmarks/`)**: Benchmark inference cycle latency, memory allocations, and serialization throughput.

---

## 2. Executing the Test Suites

Ensure the virtual environment is activated before executing tests:

```bash
source .venv/bin/activate
```

### Run All Pytest Suites:
```bash
pytest tests/ -v
```

### Run With Code Coverage Profiling:
```bash
pytest --cov=src --cov-report=term-missing --cov-report=html tests/
```

### Run Neural Model Validation Exclusively:
```bash
pytest tests/test_neural_models.py -v
```

---

## 3. Synthetic Telemetry & Deterministic Mocks

To allow testing in air-gapped environments without live traffic camera or radar feeds:

- **`SyntheticTrafficGenerator`**: Simulates realistic vehicle movements using the Greenshields model and shockwave propagation PDEs.
- **`MockHftReceiver`**: Acts as an in-memory gRPC server capturing output snapshots to verify latency and schema adherence.
- **Deterministic Random Seeds**: All neural tests fix PyTorch, NumPy, and Python seeds (`torch.manual_seed(42)`) to ensure bit-level reproducibility.

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
