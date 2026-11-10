# SYNAPSE Technical Documentation Portal

> **Master Navigation Portal for the SYNAPSE CORE Architecture Library**  
> *Noxfort Systems — A State Of Art Company*

---

> 🧭 **Quick Navigation**:
> [🏠 Synapse Core](../README.md) • [🗺️ Master MOC](SYNAPSE_MOC.md) • [🌐 Multi-Language Hub](README.md) • [🏗️ Architecture](en/architecture.md) • [🧠 Neural Models](en/neural_models.md) • [⚡ HFT-Link](en/data_ingestion_and_hft.md) • [🖥️ Desktop UI](en/ui_architecture.md)

---

## Welcome to the SYNAPSE Documentation Library

**SYNAPSE CORE v2.0** is an enterprise-grade, real-time AI perception and neural fusion platform engineered by **Noxfort Systems**. It acts as the cognitive gateway for smart city traffic infrastructures, turning disparate raw telemetry into continuous, mathematically verified traffic density fields.

### 🌐 Documentation Suites by Language

- 🇺🇸 **[English (Canonical Suite)](en/README.md)**: The authoritative, comprehensive reference manual.
- 🇧🇷 **[Português do Brasil (Suíte Completa)](pt-br/README.md)**: Documentação técnica completa em Português do Brasil para desenvolvimento e operação.
- 🇪🇸 **[Español (Suite Completa)](es/README.md)**: Documentación técnica exhaustiva para implementación en regiones de habla hispana.
- 🇫🇷 **[Français (Suite Complète)](fr/README.md)**: Guide technique complet pour le déploiement et la modélisation mathématique.
- 🇷🇺 **[Русский (Полный комплект)](ru/README.md)**: Полное техническое руководство по архитектуре, нейросетям и протоколам.
- 🇨🇳 **[简体中文 (完整技术套件)](zh/README.md)**: 面向智能交通与神经网络融合系统工程师的完整技术文档库。

---

## 🏛️ Core Technical Chapters

1. **[Core Architecture & DDD](en/architecture.md)**
   - Domain-Driven Design, Hexagonal/Clean Architecture, and process topology.
2. **[Domain Entities & Schemas](en/domain_entities.md)**
   - Topology graph nodes/edges, `SourceStatus` state machines, and Bayesian trust scores.
3. **[MARKVART™ Neural Stack](en/neural_models.md)**
   - Mathematical formulations of 10 deep networks and geometric matcher: PINO, PI-DeepONet, iTransformer, DiffusionGATv2, ModernBERT, WaveletAE-OCC.
4. **[ADAGIO™ Execution Phases](en/execution_phases.md)**
   - Structured lifecycle: Phase 0 (AutoML), Phase 1 (Golden Dataset Bootstrap), Phase 2 (Online Concurrency).
5. **[Data Ingestion & HFT-Link](en/data_ingestion_and_hft.md)**
   - Sensor adapters, Protocol Buffers (`synapse_hft.proto`), sub-250ms gRPC stream, and self-healing.
6. **[Desktop UI & Zero-Port IPC](en/ui_architecture.md)**
   - Tauri v2 + React 18 frontend with Zero-Port Stdio JSON-RPC secure communication.
7. **[Safety, Watchdog & Gating Policy](en/safety_and_watchdog.md)**
   - Out-of-process F.E.N.I.X. supervisor, drift monitoring, and multi-tiered fallback policy.
8. **[Testing & Quality Assurance](en/testing.md)**
   - Unit, integration, synthetic data generator, and high-frequency benchmarks.

---

<div align="center">
  <img src="assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
