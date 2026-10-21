# Contributing to SYNAPSE CORE

Thank you for your interest in contributing to the **SYNAPSE CORE** intelligent perception and neural fusion platform! We are building the next generation of Smart City mobility infrastructure, and peer review and community contributions are essential to our mission.

---

> 🧭 **Navigation**:
> [🏠 Synapse Core](README.md) • [🏗️ Architecture](ARCHITECTURE.md) • [📚 Developer Guide](docs/06_developer_guide.md) • [🧪 Testing](tests/README.md) • [🛡️ Security](SECURITY.md) • [📜 Code of Conduct](CODE_OF_CONDUCT.md) • [📄 License](LICENSE)

---

## 🚀 Getting Started

### 1. Fork & Clone
Fork the repository on GitHub and clone your fork locally:

```bash
git clone https://github.com/Noxfort/Synapse.git
cd Synapse
```

### 2. Configure Python Backend Environment
Ensure Python 3.10+ is installed:

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install production and development dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3. (Optional) Configure Frontend Desktop Development (Tauri v2 + React 18)
If modifying UI components, interactive map visualizers, or Rust IPC pipes:

```bash
# Install Rust toolchain
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"

# Install Node.js dependencies
npm install

# Run frontend in desktop development mode (hot-reload)
npm run tauri dev
```

For more desktop architecture specifics, refer to [`ui/README.md`](ui/README.md) and [`docs/02_ui_architecture.md`](docs/02_ui_architecture.md).

---

## 🛠️ Development Workflow

1. **Branch Naming**: Create a topic branch from `main` using descriptive prefixes:
   - `feature/` — New neural architectures, ingestion adapters, UI views.
   - `fix/` — Bug fixes, memory leak resolutions, crash remedies.
   - `docs/` — Documentation updates, mathematical clarifications.
   - `perf/` — Latency optimizations, VRAM reductions, Tensor Core tuning.
   - `test/` — Additional PyTest fixtures, benchmarks, or stress tests.

   ```bash
   git checkout -b feature/my-new-operator
   ```

2. **Making Code Changes**:
   - Strictly adhere to **SOLID** and **Domain-Driven Design (DDD)** principles.
   - All neural models must reside in [`src/models/`](docs/03_neural_models.md) and be wrapped by an agent subclassing `BaseAgent` in `src/agents/`.
   - All ingestion protocols must subclass `BaseAdapter` in `src/adapters/`.
   - Never introduce hardcoded host network ports in desktop components — communicate exclusively through [`StdioDaemon`](src/README.md#-core-subsystems-in-detail).

3. **Running the Test Suite**:
   Always verify that your changes pass all unit tests and do not introduce regressions:
   ```bash
   pytest tests/ -v
   pytest --cov=src tests/
   ```
   Refer to [`tests/README.md`](tests/README.md) for benchmark instructions.

4. **Compiling Protocol Buffers (if modifying gRPC contracts)**:
   ```bash
   python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. proto/synapse_hft.proto
   ```
   Refer to [`proto/README.md`](proto/README.md) for full Protobuf instructions.

5. **Commit Message Standards**:
   We follow [Conventional Commits](https://www.conventionalcommits.org/):
   ```text
   feat(models): implement diffusion spatial kernel in GATv2
   fix(ipc): resolve json serialization of numpy float32
   docs(arch): update high-frequency transport sequence diagram
   ```

6. **Opening a Pull Request**:
   - Push to your fork: `git push origin feature/my-new-operator`.
   - Submit a PR against the `main` branch of `Noxfort/Synapse`.
   - Fill out the [Pull Request Template](.github/PULL_REQUEST_TEMPLATE.md) completely.

---

## 📏 Code Style Guidelines

- **Python**:
  - Follow **PEP 8** strictly.
  - Enforce explicit type hinting (`typing.Optional`, `typing.Dict`, `typing.List`, `typing.Tuple`).
  - Do not mock PyTorch tensors with raw lists during tests — use `torch.randn()` with explicit `dtype` and `device`.
- **TypeScript / React**:
  - Follow strict TypeScript guidelines (`strict: true` in `tsconfig.json`).
  - Keep Zustand state stores modular and bounded by domain responsibility.
  - Use Tailwind CSS utility classes for styling consistency.

---

## 🐛 Bug Reports & Feature Requests

- **Bug Reports**: Use the [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md). Include logs from `logs/system.log` and reproducible steps.
- **Feature Requests**: Use the [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md). Provide mathematical justification or relevant research papers (arXiv) for new ML architectures.
- **Security Vulnerabilities**: **DO NOT** create public issues for security exploits. Read [`SECURITY.md`](SECURITY.md) for responsible disclosure.

---

<div align="center">
  <img src="docs/assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
