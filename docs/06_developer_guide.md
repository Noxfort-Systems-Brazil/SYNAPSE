# 06. Developer Guide

> **Development Environment Configuration, Protocol Buffers Compilation, Agent Extension, and Quality Assurance**

---

> 🧭 **Navigation**:
> [🏠 Synapse Core](../README.md) • [📚 Docs Index](README.md) • [« Previous: 05. Data Ingestion & HFT](05_data_ingestion_and_hft.md) • [Next: 07. Production Deployment »](07_deployment_guide.md)

---

## 🛠️ 1. Development Environment Setup

### Python Backend Environment
```bash
# Clone the official repository
git clone https://github.com/Noxfort/Synapse.git
cd Synapse

# Create and activate Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip and install all backend dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Desktop UI Environment (Tauri v2 + React 18)
```bash
# Ensure Rust toolchain is installed
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"

# Install frontend dependencies from root
npm install

# Or from the ui/ directory
cd ui && npm install && cd ..
```

---

## 📡 2. Modifying the HFT-Link (Protocol Buffers)

If you modify the data contracts exchanged with CARINA (e.g., adding emission metrics or pedestrian queue lengths to `proto/synapse_hft.proto`), you must recompile the Python gRPC stubs.

### Compilation Command
From the root of the repository with `.venv` active:

```bash
python -m grpc_tools.protoc \
    -I. \
    --python_out=. \
    --grpc_python_out=. \
    proto/synapse_hft.proto
```

This re-generates:
- `proto/synapse_hft_pb2.py`
- `proto/synapse_hft_pb2_grpc.py`

### Stub Import Post-Processing
The standard Google Protobuf compiler generates absolute imports in Python. If needed, verify that `proto/synapse_hft_pb2_grpc.py` imports `synapse_hft_pb2` cleanly:
```python
from proto import synapse_hft_pb2 as proto_dot_synapse__hft__pb2
```

For full protobuf specifications, refer to [`proto/README.md`](../proto/README.md).

---

## 🧪 3. Executing the QA Test Suite

SYNAPSE uses `pytest` across unit, integration, and performance benchmarking layers:

### Running Tests
```bash
# Run all unit tests
pytest tests/unit/ -v

# Run all integration tests
pytest tests/integration/ -v

# Run tests with code coverage report
pytest --cov=src --cov-report=term-missing tests/

# Execute a specific agent test suite
pytest tests/unit/test_agents.py -v
```

### Running Hardware Benchmarks
```bash
# Measure cycle latency, RAM, VRAM, and FPS with synthetic sensors
python tests/benchmark.py
```

> [!WARNING]
> Do not mock PyTorch tensors with native Python lists during tests. Always instantiate real `torch.Tensor` objects via `torch.randn(...)` with explicit `device` and `dtype` parameters to validate Tensor Core and mixed-precision acceleration paths.

---

## 🖥️ 4. Running & Building the Desktop UI

```bash
# Launch Tauri native desktop interface in hot-reload development mode
npm run tauri dev

# Type-check TypeScript and build production web bundle
npm run build

# Compile native standalone desktop executable (.deb / binary)
npm run tauri build
```

---

## 🧠 5. Adding New MARKVART™ Neural Models

1. **Define Architecture**: Add your PyTorch `nn.Module` in [`src/models/my_model.py`](03_neural_models.md).
2. **Wrap in Agent**: Create `src/agents/my_agent.py` subclassing `BaseAgent` (`src/interfaces/`).
3. **Register in Factory**: Add the model factory mapping in `src/factories/agent_factory.py`.
4. **Unit Test**: Create `tests/unit/test_my_model.py` verifying tensor shape inputs/outputs and device transitions (CPU $\leftrightarrow$ CUDA).

---

> 🧭 **Next Chapter**: Deploy SYNAPSE to production environments in [07. Production Deployment Guide](07_deployment_guide.md).

---

<p align="center">
  <sub>SYNAPSE Developer Guide — Noxfort Systems</sub><br/>
  <sub><a href="#06-developer-guide">Back to top ↑</a></sub>
</p>
