# Changelog

All notable changes to the **SYNAPSE CORE** intelligent perception and neural fusion platform will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

> 🧭 **Navigation**:
> [🏠 Synapse Core](README.md) • [🏗️ Architecture](ARCHITECTURE.md) • [📚 Docs Index](docs/README.md) • [🤝 Contributing](CONTRIBUTING.md) • [🛡️ Security](SECURITY.md) • [📜 License](LICENSE)

---

## [2.2.0] - 2026-10-21

### Added
- **Dynamic Reverse Tunneling with DuckDNS & Caddy HTTPS (`src_go/internal/tunnel/`)**:
  - Embedded high-throughput DuckDNS periodic registration driver (`duckdns.go`) updating global IPv4/IPv6 addresses every 10 minutes.
  - Native Caddy HTTPS process supervisor (`caddy.go`) dynamically compiling `config/Caddyfile` with automated Let's Encrypt / ZeroSSL TLS termination on port 443.
  - Python IPC dispatcher (`src/handlers/duckdns_handler.py`) and Desktop UI settings tab (`DuckDnsSettingsTab.tsx`).
- **ModernBERT & NeuroSymbolic Neural Pipeline (`src/models/`)**:
  - Replaced legacy DistilRoBERTa with `ModernBertEmbeddingModel` (`modernbert.py`) featuring native PyTorch SDPA attention and global Tensor Core acceleration (`allow_tf32 = True`).
  - Implemented `NeuroSymbolicModel` (`neuro_symbolic.py`) combining the ModernBERT semantic backbone with a decoupled `TCNAE` and a 3D Physics Projection Head $\mathbf{y}_{\text{phys}} = [q, v, \rho]$ bounded by LWR conservation laws.
- **Dedicated HFT Package (`src/hft/`)**:
  - Reorganized gRPC transport, streaming queue, Protobuf serializers, and self-healing auto-recovery loop into a clean architecture package (`src/hft/`).
- **Corporate Governance & Security Subsystem (`src/security/`)**:
  - Implemented multi-factor master authentication (`MasterAuth`), municipal account lifecycle (`AccountManager`), and password policy validation (`PasswordPolicy`).
  - Added brute-force lockout protection (`LockdownManager`), cryptographic security auditing (`AuditLogger`), and dual storage (`HybridSecurityRepo`).
- **ABNT Official Traffic Audit Reporting (`src/formatters/` & `src/report/`)**:
  - Automated generation of technical traffic audit documents complying with Brazilian ABNT formatting standards (`abnt_docx_exporter.py`, `abnt_html_preview_exporter.py`, `abnt_markdown_formatter.py`).
  - Dynamic typography, margins, and font configuration via `useReportTypographyStore`.
- **Small Language Model Out-of-Process Isolation (`src/slm/`)**:
  - Isolated Qwen3 LLM execution in a separate OS worker process (`IsolatedJuristManager`), ensuring generative language latency never blocks real-time PyTorch inference threads.
- **Interactive Parquet ETL Wizard & Modular Rust Services (`ui/`)**:
  - 3-step interactive import wizard (`ParquetImportModal`) with schema inspection and Ghost-File verification.
  - Modularized Tauri v2 Rust backend with dedicated native dialog services (`dialog_service.rs`) and Base64 utilities (`base64.rs`).

### Changed
- Harmonized all documentation domain entity specifications (`MapNode`, `MapEdge`, `DataSource`) with exact field signatures from `src/domain/entities.py`.
- Replaced references to legacy TimesNet with `SpectralFeatureBlock` (`src/blocks/feature_blocks.py`).
- Standardized gap imputation on `PIDeepONet` continuous operator sliding windows (`src/pipeline/imputer_pipeline.py`).

---

## [2.1.0] - 2026-10-19

### Added
- **Multi-Segment Global Feed Unpacking (`GraphManager._ingest_global_jams_feed`)**:
  - Automatic unpacking of multi-segment cloud feeds (e.g., Waze `jams` arrays) with WGS84-to-UTM projection via [`GeoProjectionService`](src/services/geo_projection_service.py) and deterministic R-Tree polyline alignment via [`FastMapMatcher`](docs/03_neural_models.md#6-fast-geometric-map-matching-deterministic-r-tree--frechet).
  - Automatic pruning of stale jammed edges when congestion clears in subsequent polling cycles.
- **8-Hop Harmonic Spatial Diffusion & Topological Conductance Prior (`FusionPipeline`)**:
  - Extended spatial propagation in [`src/pipeline/fusion_pipeline.py`](src/README.md#4-engine--high-throughput-inference-engine) to 8-hop damped harmonic graph diffusion coupled with a topological conductance/degree background prior (`y_bg`), eliminating uniform density floors on distant unobserved streets.
- **Road-Hierarchy Hydrodynamic Interpolation (`TrafficHydrodynamicEngine`)**:
  - Preserved `edge_type` (OSM/SUMO road classification) and `priority` attributes across [`MapEdge`](docs/01_domain_entities.md#2-mapedge), [`MapCommandHandler`](src/handlers/map_handler.py), and [`TopologyRepository`](src/domain/topology_repository.py).
  - Engineered 5D physical edge attribute tensors (`edge_attr` $\in \mathbb{R}^{E \times 5}$) in [`GraphTopologyBuilder`](src/managers/graph/topology_builder.py) for [`DiffusionGATv2`](docs/03_neural_models.md#5-gatv2-lite--diffusion-gatv2-topological-reasoning).
  - Weighted node-to-edge continuum interpolation by road-hierarchy permeability (`perm` $\in [0.15, 1.15]$) and continuous geometric impedance (`geom_factor`), differentiating arterial corridors from low-flow residential streets.
- **Canonical Device Alias Resolution (`IngestionHub` & `DataFlowRouter`)**:
  - Resolved external device aliases (e.g., MQTT/CSV `loop_01` $\rightarrow$ canonical `src_2` via `device_id_map`) across [`IngestionHub.route_packet`](src/adapters/ingestion_hub.py) and [`DataFlowRouter.handle_data_flow`](src/engine/data_flow_router.py), with coordinate fallback extraction for CV detection lists and inductive loop CSV rows in [`SensorElementResolver`](src/managers/graph/element_resolver.py).

### Changed
- **60-Second Global Polling Observability Window (`SnapshotBuilder`)**:
  - Extended active sensor observability horizon (`fallback_steps <= 75`) in [`SnapshotBuilder.gather_snapshot`](src/engine/snapshot_builder.py) to sustain `observability_mask = 1.0` across full 60-second global REST API polling intervals.
- **KSE UKF State Vector Synchronization (`KSEInertialImputationStrategy`)**:
  - Synchronized internal Unscented Kalman Filter state `physics_engine.x[0, 0]` during dead-reckoning projections in [`src/strategies/kse_inertial_imputation.py`](docs/04_execution_phases.md#kinematic-state-estimation-kse-dead-reckoning) to prevent unobserved nodes from freezing on static values.
- **Flow/Count Measured Speed Integration & Historical Warmup Isolation**:
  - Integrated `measured_speed_ms` into flow and passage count sensors in [`EdgeHydrodynamicsEngine`](src/managers/graph/hydrodynamics_engine.py) and isolated localized incident lists (`jams`) in [`EdgePayloadFormatter`](src/meh/edge_payload_formatter.py) during `HISTORICAL` warmup.

---

## [2.0.0] - 2026-08-30

### Added
- **Modern Desktop UI (Tauri v2 + React 18)**:
  - Replaced legacy PyQt UI with a native, high-performance [Tauri v2](ui/README.md) desktop application written in React 18, TypeScript, Tailwind CSS, and Zustand.
  - Interactive road network map visualizer ([`SumoMapCanvas`](ui/README.md#📂-frontend-directory-structure)) supporting pan, zoom, and live speed heatmaps.
  - Real-time hardware-accelerated telemetry dashboards powered by Apache ECharts.
  - Multi-language localization support ([`pt_BR`](ui/README.md#🌐-localization-i18n) and [`en_US`](ui/README.md#🌐-localization-i18n)) with instantaneous runtime switching.
- **Zero-Port Standard I/O IPC Bridge**:
  - Engineered [`StdioDaemon`](src/README.md#-core-subsystems-in-detail) running pure newline-delimited JSON-RPC over `sys.stdin`/`sys.stdout`, eliminating host network port attack vectors.
  - Rust async sidecar process manager seamlessly orchestrating the Python backend lifecycle.
- **Resilience & Self-Healing Watchdog (F.E.N.I.X.)**:
  - Added [`src/fenix/process_supervisor.py`](ARCHITECTURE.md#process-supervision-watchdog-pattern) for out-of-process health monitoring and automatic core revival.
  - Integrated `FenixDriftService` for continuous PyTorch model drift evaluation.
- **Full MARKVART™ 11-Model Ensemble**:
  - Physics-Informed Neural Operator ([`PINO-Traffic`](docs/03_neural_models.md#1-global-fusion-itransformer-itransformerpy)) with LWR conservation law constraints.
  - Continuous Field Interpolation ([`PI-DeepONet`](docs/03_neural_models.md)).
  - Inverted Multivariate Transformer ([`iTransformer`](docs/03_neural_models.md#1-global-fusion-itransformer-itransformerpy)) with spatial cross-attention.
  - Entropic Optimal Transport map matching via Sinkhorn Cross-Attention.
  - Explainable AI audit reports generated by quantized [`Qwen3`](Model_Vault/README.md#2-qwen-3-xai-jurist-agent) LLMs via `llama-cpp-python`.
- **HFT-Link gRPC Transport**:
  - Upgraded Protobuf specification to [`proto/synapse_hft.proto`](proto/README.md) with 50MB message limits and HTTP/2 streaming.
  - Automated reconnection loop ([`hft_recovery.py`](docs/05_data_ingestion_and_hft.md#auto-recovery-self-healing-loop)) re-synchronizing SUMO topologies upon controller dropouts.
- **Comprehensive QA Test Suite**:
  - Expanded test coverage across 50+ unit suites and integration benchmarks ([`tests/README.md`](tests/README.md)).
  - Hardware stress testing benchmark ([`tests/benchmark.py`](tests/README.md#1-full-hardware-stress-benchmark-testsbenchmarkpy)).

### Changed
- Standardized all domain contracts on [`src/domain/entities.py`](docs/01_domain_entities.md) with Bayesian trust hierarchy constants (`LOCAL_TRUST_SCORE = 0.95`, `GLOBAL_TRUST_SCORE = 0.60`).
- Hardened [`Phase 1 Offline Bootstrap`](docs/04_execution_phases.md#phase-1-offline-bootstrap-bootstrap_phasepy) with "Ghost File" zero-byte corruption checks for SafeTensors and Parquet Data Lakes.
- Decoupled event dispatching via `IpcEventBridge` without thread collisions.

---

## [1.0.0-rc] - 2026-04-29

### Added
- Exhaustive documentation library ([`docs/`](docs/README.md)).
- GitHub community health guidelines ([`CONTRIBUTING.md`](CONTRIBUTING.md), [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md), [`SECURITY.md`](SECURITY.md)).
- Standard GitHub issue and pull request templates ([`.github/`](.github/PULL_REQUEST_TEMPLATE.md)).

### Changed
- Replaced legacy TimeGAN implementation with `PatchTST` for temporal imputation.
- Hardened Phase 1 Bootstrap with initial data lake validation routines.
- Integrated Qwen3 1.7B prototype for legal compliance reporting.

---

<div align="center">
  <img src="docs/assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
