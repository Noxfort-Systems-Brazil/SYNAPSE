# SYNAPSE Technical Documentation Library

> **Exhaustive Architectural, Mathematical, and Operational Manuals**

---

> 🧭 **Navigation**:
> [🏠 Synapse Core](../README.md) • [🏗️ Architecture](../ARCHITECTURE.md) • [01. Entities](01_domain_entities.md) • [02. UI](02_ui_architecture.md) • [03. Neural Models](03_neural_models.md) • [04. Phases](04_execution_phases.md) • [05. HFT](05_data_ingestion_and_hft.md) • [06. Dev Guide](06_developer_guide.md) • [07. Deploy](07_deployment_guide.md)

---

## 📚 Technical Documentation Index

Welcome to the comprehensive technical documentation library for **SYNAPSE CORE v2.0**. This library provides deep-dive guides into every subsystem of the platform, designed to be browsed seamlessly both on **GitHub** and inside an **Obsidian** knowledge vault.

---

### 📖 Available Guides

| Chapter | Document Link | Description & Key Topics |
| :--- | :--- | :--- |
| **01. Domain Entities** | [01_domain_entities.md](01_domain_entities.md) | `MapNode`, `MapEdge`, `DataSource`, `SourceStatus` state machines, zero-trust lifecycle, and Bayesian trust hierarchy constants. |
| **02. UI Architecture** | [02_ui_architecture.md](02_ui_architecture.md) | Modern desktop UI design, Tauri v2 Rust sidecar manager, React 18 frontend, Zustand reactive stores, and Zero-Port Stdio IPC. |
| **03. Neural Models & Math** | [03_neural_models.md](03_neural_models.md) | Complete mathematical formulations, loss functions, and PyTorch implementations of the 11 MARKVART™ models (PINO, DeepONet, iTransformer, GATv2, VAE-TCN). |
| **04. Execution Phases** | [04_execution_phases.md](04_execution_phases.md) | ADAGIO™ lifecycle (Phase 0 AutoML, Phase 1 Bootstrap Golden Dataset, Phase 2 Online 4-Thread Concurrency Runtime, KSE Dead Reckoning). |
| **05. Data Ingestion & HFT** | [05_data_ingestion_and_hft.md](05_data_ingestion_and_hft.md) | Sensor adapters (HTTP, MQTT, WebSocket), Protocol Buffers (`proto/synapse_hft.proto`), gRPC streaming, and background self-healing auto-recovery loops. |
| **06. Developer Guide** | [06_developer_guide.md](06_developer_guide.md) | Setting up development environments, compiling Protobuf schemas, extending agents, and executing PyTest suites. |
| **07. Production Deployment** | [07_deployment_guide.md](07_deployment_guide.md) | Headless daemon configuration, `systemd` unit setup, Docker containerization, Debian packaging, and Prometheus/Grafana monitoring. |

---

## 🧭 Suggested Reading Paths

### 🧠 For Machine Learning & Research Engineers:
1. [01. Domain Entities & Core Structures](01_domain_entities.md)
2. [03. Neural Models & PyTorch Implementations (MARKVART™)](03_neural_models.md)
3. [04. Execution Phases & Lifecycle (ADAGIO™)](04_execution_phases.md)
4. [Model Vault Weights & LLM Assets](../Model_Vault/README.md)

### ⚙️ For Systems & Backend Engineers:
1. [01. Domain Entities & Core Structures](01_domain_entities.md)
2. [05. Data Ingestion & HFT Network](05_data_ingestion_and_hft.md)
3. [06. Developer Guide](06_developer_guide.md)
4. [07. Production Deployment Guide](07_deployment_guide.md)
5. [HFT Protocol Buffers Specification](../proto/README.md)
6. [Backend Core Architecture Guide](../src/README.md)

### 🖥️ For Frontend & Desktop Engineers:
1. [01. Domain Entities & Core Structures](01_domain_entities.md)
2. [02. UI Architecture & Modern Frontend](02_ui_architecture.md)
3. [Desktop UI Technical Manual](../ui/README.md)

### 🧪 For QA & Site Reliability Engineers:
1. [Testing & Quality Assurance Suite](../tests/README.md)
2. [Observability & Monitoring Stack](../observability/README.md)
3. [Packaging & Debian Distribution](../packaging/README.md)

---

<p align="center">
  <sub>SYNAPSE Documentation — Noxfort Systems Engineering Library</sub><br/>
  <sub><a href="#synapse-technical-documentation-library">Back to top ↑</a></sub>
</p>
