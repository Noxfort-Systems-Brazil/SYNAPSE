---
name: Bug report
about: Create a report to help us improve the SYNAPSE architecture
title: '[BUG] '
labels: 'bug, needs triage'
assignees: ''

---

**Describe the bug**
A clear and concise description of what the bug is.

**Affected Subsystem**
- [ ] Ingestion Hub / Adapters (`src/adapters/`)
- [ ] MARKVART™ Neural Models (`src/models/` or `src/agents/`)
- [ ] Real-time Engine & Cycle Processor (`src/engine/`)
- [ ] HFT-Link gRPC Transport (`src/infrastructure/` or `proto/`)
- [ ] Tauri v2 / React 18 Desktop Frontend (`ui/`)
- [ ] Zero-Port Stdio IPC Daemon (`src/ipc/`)
- [ ] F.E.N.I.X. Supervisor / Resilience (`src/fenix/` or `src/afb/`)

**To Reproduce**
Steps to reproduce the behavior:
1. Boot SYNAPSE using command: `...`
2. Configure or inject data: `...`
3. Advance to ADAGIO™ phase: `...`
4. Observe the failure or crash.

**Expected behavior**
A clear and concise description of what you expected to happen.

**Execution Logs**
```text
# Paste relevant output from logs/system.log or terminal console
```

**Environment Information:**
- **Operating System**: [e.g. Ubuntu 22.04 LTS x86_64]
- **Python Version**: [e.g. 3.10.12]
- **PyTorch / CUDA Version**: [e.g. PyTorch 2.2.0 + CUDA 12.1]
- **NVIDIA Driver**: [e.g. 535.129.03]
- **Node.js & Rust (if UI bug)**: [e.g. Node v20.11, rustc 1.77.0]

**Additional Context**
Add any other context about the problem here (e.g. sensor schema format, dropped packet frequency, SUMO `.net.xml` size).
