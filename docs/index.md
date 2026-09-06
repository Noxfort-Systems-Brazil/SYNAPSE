# SYNAPSE Technical Documentation Index

> **Master Navigation Portal for the SYNAPSE CORE Architecture Library**

---

> 🧭 **Navigation**:
> [🏠 Synapse Core](../README.md) • [🏗️ Architecture](../ARCHITECTURE.md) • [01. Entities](01_domain_entities.md) • [02. UI](02_ui_architecture.md) • [03. Neural Models](03_neural_models.md) • [04. Phases](04_execution_phases.md) • [05. HFT](05_data_ingestion_and_hft.md) • [06. Dev Guide](06_developer_guide.md) • [07. Deploy](07_deployment_guide.md)

---

## The Technical Library

Welcome to the documentation library for **SYNAPSE CORE v2.0**. For high-level overviews, please explore the root [`README.md`](../README.md) and [`ARCHITECTURE.md`](../ARCHITECTURE.md).

### Chapters

1. **[01. Domain Entities & Core Structures](01_domain_entities.md)**
   - Detailed mapping of `src/domain/entities.py`.
   - The Bayesian Trust Score hierarchy (`LOCAL_TRUST_SCORE = 0.95`, `GLOBAL_TRUST_SCORE = 0.60`).
   - The `SourceStatus` state machine (`QUARANTINE` $\rightarrow$ `VALIDATING` $\rightarrow$ `ACTIVE` $\rightleftharpoons$ `FALLBACK`).

2. **[02. UI Architecture & Modern Frontend](02_ui_architecture.md)**
   - Native desktop application engineered with Tauri v2 + React 18 + TypeScript + Tailwind CSS.
   - Zero-Port Stdio JSON-RPC IPC bridge communicating with Python backend.
   - Zustand state stores (`useSensorsStore`, `useTopologyStore`, `useSystemStore`, `useXaiStore`).

3. **[03. Neural Models & Math (MARKVART™)](03_neural_models.md)**
   - Mathematical formulations of all 11 neural architectures.
   - Low-level PyTorch implementations: `PINO-Traffic`, `PI-DeepONet`, `iTransformer`, `GATv2 Lite`, `TCNAE`, `WaveletAE-OCC`, `PatchTST`, and `Qwen3`.

4. **[04. Execution Phases (ADAGIO™)](04_execution_phases.md)**
   - Structured lifecycle: Phase 0 (Optuna AutoML), Phase 1 (Offline Bootstrap Golden Dataset with Ghost-File Protection), Phase 2 (Online 4-Thread Concurrency Runtime).
   - Kinematic State Estimation (KSE) Dead Reckoning for packet drops.

5. **[05. Data Ingestion & HFT Network](05_data_ingestion_and_hft.md)**
   - Ingestion adapters (HTTP push/poll, MQTT, WebSocket).
   - High-Frequency Transport (gRPC) streaming via Protocol Buffers (`proto/synapse_hft.proto`).
   - Self-healing background auto-recovery loops (`hft_recovery.py`).

6. **[06. Developer Guide](06_developer_guide.md)**
   - Setting up backend Python and frontend desktop development environments.
   - Compiling HFT-Link Protobuf definitions.
   - Executing the PyTest suite and test coverage profiling.

7. **[07. Production Deployment Guide](07_deployment_guide.md)**
   - Running SYNAPSE securely in Headless Daemon mode (`python synapse.py --daemon`).
   - Setting up `systemd` services and automated log rotation.
   - Running the F.E.N.I.X. watchdog supervisor (`python synapse.py --supervisor`).

---

<p align="center">
  <sub>SYNAPSE Master Index — Noxfort Systems</sub><br/>
  <sub><a href="#synapse-technical-documentation-index">Back to top ↑</a></sub>
</p>
