---
tags: [moc, hub, docs, obsidian, synapse, index]
aliases: [SYNAPSE MOC, Master Documentation Hub, Documentation Index, Knowledge Vault]
---

# 📚 SYNAPSE Technical Master Documentation Hub (MOC)

Welcome to the **SYNAPSE** (Intelligent Perception & Neural Fusion Gateway for Smart City Traffic Management) master documentation library. Designed as an asynchronous, ultra-high-frequency cognitive platform, SYNAPSE ingests multimodal municipal sensory streams, orchestrates the **MARKVART™** 10-neural network ensemble, executes **ADAGIO™** phase transitions, and feeds clean macroscopic traffic matrices downstream to **CARINA** controllers via **HFT-Link** gRPC.

This Map of Content (MOC) provides technical taxonomy and direct paths for core developers, machine learning researchers, traffic engineers, and systems operators. It is fully compatible with both **GitHub** and **[Obsidian](https://obsidian.md/)**.

---

## 🗺️ Codebase Map & Directory Hierarchy

```text
SYNAPSE_CORE/
├── synapse.py                  # Master CLI Entrypoint (--daemon, --supervisor, --phase, etc.)
├── ARCHITECTURE.md             # Low-Level Architectural Blueprint & Data Flow
├── mkdocs.yml                  # Material for MkDocs Configuration
├── pyproject.toml              # Build toolchain & project metadata
├── requirements.txt            # Python runtime dependencies
├── .env.example                # 12-Factor App environment configuration
│
├── bin/                        # Compiled high-performance binaries (synapse-gateway, caddy)
├── config/                     # Configuration files (settings.ini, Caddyfile, report templates)
│
├── proto/                      # Protocol Buffers v3 Specifications
│   ├── README.md               # gRPC HFT-Link Architecture Manual
│   └── synapse_hft.proto       # High-Frequency Snapshot, Edge, Matrix Protobuf Definitions
│
├── docs/                       # Comprehensive Knowledge Vault
│   ├── README.md               # Central Multi-Language Documentation Hub
│   ├── SYNAPSE_MOC.md          # Master Map of Content (This File)
│   ├── index.md                # MkDocs Entry Point & Master Index
│   ├── stylesheets/extra.css   # Custom CSS branding
│   ├── assets/                 # Brand and logo imagery
│   │
│   ├── en/                     # 🇺🇸 Canonical English Documentation Suite
│   │   ├── README.md           # English Hub & Reading Paths
│   │   ├── architecture.md     # Clean Architecture, DDD, & Component Topology
│   │   ├── domain_entities.md  # MapNode, MapEdge, Bayesian Trust & State Machines
│   │   ├── neural_models.md    # 10 MARKVART™ Models, PDEs, and PyTorch Formulations
│   │   ├── execution_phases.md # ADAGIO™ Phases 0, 1, 2, Runtime Concurrency & KSE
│   │   ├── data_ingestion_and_hft.md # Ingestion Hub, gRPC HFT-Link & Self-Healing
│   │   ├── ui_architecture.md  # Tauri v2, React 18, Zustand & Zero-Port Stdio IPC
│   │   ├── safety_and_watchdog.md # F.E.N.I.X. Supervisor, Drift Monitor & Gating
│   │   └── testing.md          # Pytest Suite, Mocks, Benchmarks & Profiling
│   │
│   ├── pt-br/                  # 🇧🇷 Suíte Completa em Português do Brasil
│   ├── es/                     # 🇪🇸 Suite Completa en Español
│   ├── fr/                     # 🇫🇷 Suite Complète en Français
│   ├── ru/                     # 🇷🇺 Полный комплект на Русском языке
│   └── zh/                     # 🇨🇳 简体中文完整技术套件
│
├── src/                        # Python Core Cognitive Backend
│   ├── README.md               # Backend Architecture Guide
│   ├── domain/                 # Domain Entities (MapNode, MapEdge, AppState, Trust Scores)
│   ├── models/                 # Pure PyTorch Neural Implementations (ModernBERT, PINO, DeepONet, iTrans)
│   ├── agents/                 # Autonomous MARKVART™ Model Orchestration Agents
│   ├── blocks/                 # Modular Deep Learning Blocks (Spectral, Graph, Temporal)
│   ├── controllers/            # Hexagonal Application Controllers
│   ├── database/               # Connection Pool Proxy, Engine, Migrations & Settings
│   ├── engine/                 # Real-time Inference Engine & Routing
│   ├── fenix/                  # F.E.N.I.X. Drift Monitor & Out-of-Process Watchdog
│   ├── formatters/             # ABNT Official Report Formatters (DOCX, HTML, Markdown)
│   ├── go/                     # Subprocess Lifecycle & Anonymous Pipe Transport for synapse-gateway
│   ├── handlers/               # Command, Database, DuckDNS, Map, and Parquet Handlers
│   ├── hft/                    # High-Frequency Transport (gRPC Client, Streamer, Auto-Recovery)
│   ├── infrastructure/         # PostgreSQL Data Lake, SafeTensors IO, Network Services
│   ├── ipc/                    # StdioDaemon, JSON-RPC Bridge, Event Routing
│   ├── kse/                    # Kinematic State Estimation (Kalman Dead Reckoning)
│   ├── linguist/               # Global Cartographer, Compass Reconciler, Topology Matcher
│   ├── phases/                 # ADAGIO™ Phases (AutoML, Bootstrap, Online 4-Thread)
│   ├── physics/                # LWR Equations & Greenshields Fundamental Diagrams
│   ├── pipeline/               # Multi-Agent Fusion, Specialist, Jurist, Imputer Pipelines
│   ├── report/                 # Traffic Kinematics, Jurist Diagnosis, Network Summaries
│   ├── security/               # MasterAuth, AccountManager, PasswordPolicy, LockdownManager
│   ├── services/               # Internal Domain Services (FastMapMatcher, MapService)
│   ├── slm/                    # Small Language Model Isolation Subsystem (IsolatedJuristManager)
│   └── storage/                # Checkpoint Store, Path Scaffolder, Snapshot Store, Vault Sync
│
├── ui/                         # Desktop Application (Tauri v2 + React 18)
│   ├── README.md               # Frontend Engineering Manual
│   ├── src-tauri/              # Rust Native Backend, Sidecar Manager, IPC Pipes, Native Dialog Services
│   └── src_ui/                 # React 18, TypeScript, Tailwind CSS, Zustand, ECharts, ABNT Reports
│
├── Model_Vault/                # Pre-trained Weights & Quantized Models
│   └── README.md               # SafeTensors & Tokenizer Weights Catalog
├── observability/              # Prometheus, Grafana & Metrics Exporting
│   └── README.md               # Observability Infrastructure
├── src_go/                     # High-Performance Sensor Ingestion Gateway & HTTPS/DuckDNS Tunnel
│   └── README.md               # Go Gateway & Reverse Tunnel Manual
└── tests/                      # Pytest Suites, Synthetic Data & Benchmarks
    └── README.md               # QA & Testing Guide
```

---

## 🏛️ Subsystem Deep Dives

### 1. Domain-Driven Design & State Machines
- **Source of Truth**: [Domain Entities Specification](en/domain_entities.md)
- **Key Concepts**: `MapNode` (projected metric UTM x, y coordinates), `MapEdge` (5D physical attributes and hierarchy), `DataSource`, `SourceStatus` state lifecycle (`QUARANTINE` $\rightarrow$ `VALIDATING` $\rightarrow$ `ACTIVE` $\rightleftharpoons$ `FALLBACK`).
- **Trust Scores**: Local ground-truth sensors initialized at $0.95$, third-party APIs at $0.60$.

### 2. MARKVART™ Neural Stack (10 Deep Networks & Geometric Matcher)
- **Source of Truth**: [Neural Models & Mathematical Formulations](en/neural_models.md)
- **Continuum Operators**: PINO-Traffic (Fourier Neural Operator constrained by LWR PDE), PI-DeepONet (dual-network branch/trunk for field estimation and continuous gap imputation).
- **Time-Series Transformers**: iTransformer (inverted dimension-centric attention over time tokens).
- **Spatial & Topological Reasoning**: GATv2 Lite, Diffusion GATv2 (5D edge tensor with 8-hop harmonic graph diffusion), FastMapMatcher (deterministic CPU R-Tree + Fréchet alignment).
- **Anomaly & Gatekeeping**: ModernBERT & NeuroSymbolicModel (with 3D Physics Projection Head $[q, v, \rho]$), WaveletAE-OCC, PI-DVAE-TCN.
- **Cognitive Justification**: Qwen3 Jurist (isolated SLM sub-process execution).

### 3. ADAGIO™ Lifecycle & Kinematic Dead Reckoning
- **Source of Truth**: [Execution Phases & ADAGIO™](en/execution_phases.md)
- **Phase 0**: Hyperparameter optimization via Optuna AutoML.
- **Phase 1**: Offline bootstrap generating the Golden Dataset with ghost-file anti-corruption guards.
- **Phase 2**: Online 4-thread runtime concurrency architecture.
- **Kinematic State Estimation (KSE)**: Kalman-based dead reckoning filling telemetry gaps when packet loss occurs.

### 4. High-Frequency Ingestion & Reverse Tunneling
- **Source of Truth**: [Data Ingestion & HFT-Link](en/data_ingestion_and_hft.md)
- **Protobuf Schemas**: [`proto/synapse_hft.proto`](../proto/synapse_hft.proto) and [`src/hft/`](../src/README.md).
- **Streaming Pipeline**: Sub-250ms latency snapshot transmission to CARINA controllers with automatic reconnect and backoff.
- **Go Gateway & Reverse Tunnel**: Compiled `synapse-go` socket ingestion daemon with embedded DuckDNS dynamic IP updater and Caddy automatic Let's Encrypt HTTPS reverse proxy.

### 5. Desktop Application & Zero-Port Stdio IPC
- **Source of Truth**: [UI Architecture & Desktop Manual](en/ui_architecture.md)
- **Zero-Port Security**: Stdio newline-delimited JSON-RPC communication without exposing open network ports.
- **Frontend Stack**: Tauri v2, Rust sidecar orchestrator, React 18, Zustand stores, and dynamic ECharts visualization.

### 6. Safety Watchdog & Gating Policy
- **Source of Truth**: [Safety, Watchdog & Gating Policy](en/safety_and_watchdog.md)
- **F.E.N.I.X. Supervisor**: Out-of-process watchdog detecting process failure and initiating seamless resurrection.
- **Gating Policy**: Multi-tiered fallback strategy (Neural $\rightarrow$ KSE $\rightarrow$ Historical).

---

<div align="center">
  <img src="assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
