# SYNAPSE Core — Backend Architecture & Subsystems

> **Internal Architecture Guide for Python Core Services, Neural Inference, and Domain Logic**

---

> 🧭 **Navigation**:
> [🏠 Synapse Core](../README.md) • [🏗️ Architecture](../ARCHITECTURE.md) • [📚 Docs Index](../docs/README.md) • [🧠 Neural Models](../docs/03_neural_models.md) • [⚡ HFT-Link](../proto/README.md) • [🖥️ Desktop UI](../ui/README.md) • [🧪 Testing](../tests/README.md)

---

## 🏛️ Architectural Principles

The backend of **SYNAPSE CORE** is engineered in Python 3.10+ with PyTorch 2.x, adhering to **Domain-Driven Design (DDD)**, **Clean Architecture**, and strict **SOLID** patterns:

1. **Single Responsibility Principle (SRP)**: Every module, service, agent, and pipeline encapsulates a single bounded responsibility.
2. **Open/Closed Principle (OCP)**: New sensors, neural architectures, and optimization strategies are added via abstract interfaces without modifying existing pipelines.
3. **Liskov Substitution Principle (LSP)**: All neural agents implement `BaseAgent`, and all ingestion protocols implement `BaseAdapter`.
4. **Interface Segregation Principle (ISP)**: Interfaces in `src/interfaces/` are finely segregated (e.g., `IEngine`, `INode`, `IMemory`, `ITransport`).
5. **Dependency Inversion Principle (DIP)**: High-level orchestrators depend upon abstract interfaces and receive repositories via Constructor Injection (`ServiceContainer` and `ControllerFactory`).

---

## 📦 Subsystem Directory Breakdown

The `src/` directory contains 35 specialized packages organized into logical architectural layers:

```text
src/
├── [domain/](../docs/01_domain_entities.md)      # Core business entities, AppState facade, repositories
├── [models/](../docs/03_neural_models.md)      # PyTorch neural network & operator implementations
├── agents/            # MARKVART™ autonomous neural agents & model wrappers
├── blocks/            # Deep learning building blocks (Graph, Spectral, Temporal)
├── physics/           # Continuum traffic physics, LWR PDEs, fundamental diagrams
├── engine/            # Real-time inference engine, cycle runner, and routing
├── node/              # TrafficNode graph vertices, state, and step processing
├── pipeline/          # Agent-specific execution pipelines
├── stages/            # ADAGIO execution stages (Auditor, Classification, Sanitization)
├── strategies/        # Validation, imputation, clustering, and ensemble strategies
├── [phases/](../docs/04_execution_phases.md)      # ADAGIO™ lifecycle phases (Optimization, Bootstrap, Runtime)
├── orchestrators/     # HFT and lifecycle orchestrators
├── workers/           # Background thread workers (Ingestion, XAI, Standby)
├── ipc/               # Headless StdioDaemon, JSON-RPC protocol, EventBridge
├── [adapters/](../docs/05_data_ingestion_and_hft.md)    # Ingestion adapters (HTTP Push/Poll, MQTT, WebSocket, Replay)
├── infrastructure/    # gRPC client, PostgreSQL manager, SafeTensors storage
├── kse/               # Kinematic State Estimation (Kalman Dead Reckoning)
├── afb/               # Adaptive Fallback Engine & SensorGuard
├── meh/               # Micro-Estimation History & Golden Dataset loader
├── fenix/             # F.E.N.I.X. drift evaluation & out-of-process supervisor
├── memory/            # Episodic, Semantic, Spatial, and Spatiotemporal memory
├── optimization/      # Optuna AutoML and Bayesian Hyperparameter Tuning
├── trainer/           # Neural training routines for agents
├── factories/         # Factory methods & ServiceContainer for IoC
├── handlers/          # Command and database event handlers
├── managers/          # Graph, Node, Source, Storage, and XAI managers
├── services/          # Domain services (MapService, LinguistService, FenixService)
├── interfaces/        # Abstract Base Classes and Typing Protocols
├── prompts/           # LLM Jinja2 prompt configurations (Multi-language)
├── templates/         # Prompt templates for Jurist XAI reports
├── logging/           # Centralized logging facade and interceptors
└── utils/             # Hardware acceleration, geometry, normalization helpers
```

---

## 🔬 Core Subsystems in Detail

### 1. `domain/` — The Core Domain Model
- **`entities.py`**: Defines core dataclasses ([`DataSource`, `MapNode`, `MapEdge`, `DataAssociation`](../docs/01_domain_entities.md)), including road hierarchy attributes (`edge_type`, `priority`, `signal_group_id`).
- **`app_state.py`**: Thread-safe Domain Facade protecting `TopologyRepository` and `SourceRepository`. Ensures atomic state transitions.
- **`source_repository.py` & `topology_repository.py`**: In-memory, zero-trust repositories storing sensors and the SUMO graph with full OSM road classification metadata.
- **`model_contracts.py`**: Data contracts and tensor shapes passed between neural models.

### 2. `models/` — Pure PyTorch Neural Operators & Transformers
- **`pino_traffic.py`**: Physics-Informed Neural Operator utilizing Fourier Spectral Convolutions and LWR conservation laws.
- **`pi_deeponet.py`**: Dual-network Branch/Trunk Deep Operator Network for continuous spatial-temporal field interpolation.
- **`pi_dvae_tcn.py`**: Denoising Variational Autoencoder with Dilated Causal Convolutions for trajectory correction.
- **`itransformer.py`**: Inverted Multi-Variate Transformer embedding time-series as tokens with spatial cross-attention.
- **`gatv2_lite.py` & `diffusion_gatv2.py`**: Dynamic Graph Attention Networks operating over 5D physical edge attributes (`edge_attr`) with anisotropic spatial diffusion.
- **`wavelet_ae_occ.py`**: Discrete Wavelet Transform Autoencoder with One-Class Deep SVDD anomaly score.
- **`tcn_ae.py`**: Temporal Convolutional Autoencoder for local sensor temporal embedding.
- Complete mathematics in [`docs/03_neural_models.md`](../docs/03_neural_models.md).

### 3. `agents/` — MARKVART™ Autonomous Neural Agents
Each agent wraps one or more models from `models/`, managing tensor preparation, device allocation, inference, and online adaptation:
- `SpecialistAgent`: Runs local TCN inference per active sensor.
- `CorrectorAgent`: Runs PI-VAE-TCN to clean noisy readings.
- `LinguistAgent`: Performs semantic validation and schema detection on incoming feeds.
- `CoordinatorAgent`: Aggregates spatial graph context via GATv2.
- `FuserAgent`: Fuses all embeddings into the global "Perfect Snapshot" matrix using iTransformer and PINO.
- `TranslationAgent`: Uncovers cyclical frequency patterns via TimesNet (FFT).
- `ImputerAgent`: Generates synthetic traffic sequences for dead sensors via PatchTST.
- `AuditorAgent`: Flags out-of-distribution patterns using WaveletAE-OCC.
- `PeakClassifierAgent`: Identifies peak/off-peak schedules using ModernBERT + GMM.
- `JuristAgent`: Produces explainable XAI audit reports via quantized Qwen3 LLMs.

### 4. `engine/` & `pipeline/` — High-Throughput Inference & Spatial Fusion
- **`inference_engine.py`**: Coordinates the tick execution loop across all active nodes and agents.
- **`cycle_processor.py`**: Executes cycle-level tensor concatenation, batching, and fallback dispatching.
- **`snapshot_builder.py`**: Gathers node embeddings, KSE velocity/acceleration states, and `direct_edge_metrics`, sustaining active sensor observability (`fallback_steps <= 75`) across 60s global polling cycles.
- **`fusion_pipeline.py`**: Combines `DiffusionGATv2` attention with 8-hop damped harmonic graph diffusion and a topological conductance prior (`y_bg`) to reconstruct densities across unobserved junctions.
- **`data_flow_router.py`**: Resolves canonical sensor IDs (`device_id_map`), converts raw payloads to SI units, and dispatches updates to `GraphManager`.
- **`gating_policy.py`**: Decides whether a node's output should be sourced from Neural Inference, KSE Dead Reckoning, or MEH Historical Lookup.

### 5. `physics/` & `managers/graph/` — Continuum Mechanics, Hierarchy Hydrodynamics & Queues
- **`traffic_hydrodynamics.py`**: `TrafficHydrodynamicEngine` solving LWR/Greenshields edge states and interpolating unobserved edges using OSM/SUMO road-hierarchy permeability (`edge_type`, `priority`) and geometric impedance.
- **`queue_dynamics.py`**: `TrafficQueueCalculator` computing physical vehicle storage capacity and queue lengths at signalized and unsignalized bottlenecks.
- **`managers/graph/hydrodynamics_engine.py`**: `EdgeHydrodynamicsEngine` converting speed, flow, and passage count telemetry (with `measured_speed_ms`) into continuum edge kinetics.
- **`managers/graph/payload_extractor.py` & `element_resolver.py`**: Multi-format telemetry extraction (JSON, CV recognition lists, inductive loop CSVs) and R-Tree/coordinate element resolution.
- **`continuum.py` & `fundamental_diagrams.py`**: Spatial graph conservation equations and Greenshields/Greenberg/Underwood fundamental curves ($q = k \cdot v$).
- **`sensor_physical_validator.py` & `traffic_loss.py`**: Hard physical boundary checks and PDE residual loss penalties $\mathcal{L}_{PINO} = \mathcal{L}_{data} + \lambda \mathcal{L}_{physics}$.

### 6. `ipc/` — Headless Daemon & Sidecar Bridge
- **`stdio_daemon.py`**: Zero-port IPC server listening to JSON-RPC on `sys.stdin` and emitting events to `sys.stdout`. Uses `QCoreApplication` strictly as an event loop (no GUI dependencies).
- **`stdio_transport.py`**: High-performance, non-blocking standard I/O stream handler.
- **`command_router.py`**: Dispatches incoming desktop UI commands to domain handlers.
- **`event_bridge.py`**: Bridges internal signals and telemetry events to frontend IPC payloads.

### 7. `go/` — Go Gateway IPC Subprocess Management
- **`binary_manager.py`**: Binary compilation and lifecycle manager for `synapse-gateway`.
- **`pipe_process.py`**: Subprocess execution and line-buffered anonymous `STDIN`/`STDOUT` pipe communication.
- **`pipe_dispatcher.py`**: Event-driven NDJSON packet dispatcher with extensible event handlers (OCP).
- **`subprocess_transport.py`**: Pure Facade coordinating binary lifecycle, pipe process, and event dispatching.

### 8. `hft/` — High-Frequency Transport (CARINA gRPC Link)
- **`grpc_connector.py`**: Pure Facade orchestrating CARINA HFT streaming, lifecycle, and recovery.
- **`hft_grpc_client.py`**: Low-level gRPC channel, stub, and RPC client.
- **`hft_streamer.py`**: Non-blocking frame queue with 150ms batch throttling and 250ms heartbeats.
- **`hft_recovery.py`**: Self-healing background auto-recovery worker that re-establishes dropped gRPC connections and re-syncs maps.
- **`hft_serializers.py`**: Protobuf serializers for scenarios and traffic frames.

### 9. `infrastructure/` — Storage & Persistence I/O
- **`sensor_gateway.py`**: Unified gateway for physical and simulated data sources.
- **`postgres_manager.py`**: PostgreSQL database connector for historical persistence.
- **`safetensors_repository.py`**: Zero-copy tensor persistence using the HuggingFace `safetensors` format.
- **`json_source_storage.py`**: Local JSON persistence for data sources and configurations.
- **`parsers.py`**: Ingestion payload parsers and polyglot deserializers.
- **`sensor_id_extractor.py`**: Dynamic sensor ID heuristic extraction.

### 10. `afb/`, `kse/`, `meh/`, & `fenix/` — Resilience Quadriad
- **`kse/` (Kinematic State Estimation)**: Extended Kalman Filtering and dead reckoning estimating vehicle counts and queue lengths during network packet drops.
- **`meh/` (Micro-Estimation History)**: High-resolution historical lookup tables extracted from the Golden Dataset.
- **`afb/` (Adaptive Fallback System)**: Fault-tolerant sensor protection engine that dynamically downgrades failing sensors from `ACTIVE` to `FALLBACK` and recovers them through `PROBATION`.
- **`fenix/`**: Long-term model drift monitoring, maintenance scheduling, and out-of-process watchdog supervision (`process_supervisor.py`).

---

## 🔄 End-to-End Processing Cycle

A single real-time cycle (typically 1.0 second) executes in strictly orchestrated steps:

```text
1. INGESTION       Raw sensor JSON/MQTT payload arrives at IngestionHub.
2. ZERO-TRUST      Linguist Agent checks schema & physics validity.
3. DEAD RECKONING  KSE Module updates kinematic predictions if packet was delayed.
4. LOCAL EMBED     Specialist Agents execute TCN-AE across active sensor nodes.
5. TOPOLOGY        Coordinator Agent runs GATv2 over the SUMO graph.
6. GLOBAL FUSION   iTransformer + PINO fuse spatial-temporal tokens into Snapshot.
7. AUDIT & XAI     WaveletAE checks anomaly scores; Jurist compiles log if anomalous.
8. HFT TRANSPORT   State is serialized into Protobuf and pushed to CARINA via gRPC.
9. IPC TELEMETRY   EventBridge pushes metrics to Tauri desktop UI via JSON-RPC.
```

---

## 🧵 Concurrency & Threading Model

SYNAPSE executes with a dedicated multi-threaded concurrency architecture:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   MAIN THREAD (Headless Event Core)                    │
│     - QCoreApplication Event Loop & StdioDaemon JSON-RPC Transport     │
│     - SignalRouter dispatching async internal signals                  │
└───────────────┬────────────────────────────────────────┬───────────────┘
                │ Spawns & Coordinates                   │
┌───────────────▼───────────────┐        ┌───────────────▼───────────────┐
│     Ingestion Worker Thread   │        │   Standby Linguist Thread     │
│  - Consumes HTTP, MQTT, WS    │        │  - Validates quarantined feeds│
│  - Pushes raw queues          │        │  - Runs ModernBERT embed      │
└───────────────────────────────┘        └───────────────────────────────┘
┌───────────────────────────────┐        ┌───────────────────────────────┐
│   Neural Core Engine Thread   │        │     XAI Jurist Worker Thread  │
│  - PyTorch CUDA inference     │        │  - Non-blocking LLM reports   │
│  - KSE Kalman Dead Reckoning  │        │  - Multi-language template gen│
│  - HFT-Link gRPC transmission │        │                               │
└───────────────────────────────┘        └───────────────────────────────┘
```

---

## 🛠️ Developer Guidelines: Adding New Models & Services

### Adding a New Neural Model:
1. Define the PyTorch architecture in [`src/models/my_model.py`](../docs/03_neural_models.md) (ensure `torch.backends.cuda.matmul.allow_tf32 = True` for Tensor Core support).
2. Create the corresponding Agent in `src/agents/my_agent.py` inheriting from `BaseAgent`.
3. Register the agent factory in `src/factories/agent_factory.py`.
4. Add unit and integration tests under `tests/unit/test_my_agent.py`.

### Adding a New Data Ingestion Protocol:
1. Subclass `BaseAdapter` in [`src/adapters/my_adapter.py`](../docs/05_data_ingestion_and_hft.md).
2. Register the protocol in [`src/domain/entities.py`](../docs/01_domain_entities.md) (`SourceType`).
3. Connect the adapter inside `src/adapters/ingestion_hub.py`.

---

<div align="center">
  <img src="../docs/assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
