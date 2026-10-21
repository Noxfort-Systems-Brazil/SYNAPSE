<div align="center">

<img src="../assets/synapse-logo.png" alt="SYNAPSE CORE Logo" width="120" />

# SYNAPSE — Technical Documentation Suite (English)
### System Architecture, Neural Fusion & Smart City Perception
*Noxfort Systems — A State Of Art Company*

[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat&logo=github)](https://github.com/Noxfort-Systems-Brazil/SYNAPSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)](https://python.org/)
[![Rust](https://img.shields.io/badge/Rust-1.75%2B-DEA584?style=flat&logo=rust&logoColor=white)](https://rust-lang.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-EE4C2C?style=flat&logo=pytorch&logoColor=white)](https://pytorch.org/)

---

🌐 **Languages:** **[🇺🇸 English](README.md)** • **[🇧🇷 Português](../pt-br/README.md)** • **[🇪🇸 Español](../es/README.md)** • **[🇫🇷 Français](../fr/README.md)** • **[🇷🇺 Русский](../ru/README.md)** • **[🇨🇳 简体中文](../zh/README.md)** • **[📚 Central Hub](../README.md)**

---

</div>

## Welcome to the Official Canonical Documentation

This directory contains the authoritative technical documentation in **English** for **SYNAPSE CORE** (Intelligent Perception & Neural Fusion Gateway for Smart City Traffic Management). SYNAPSE processes asynchronous municipal sensory feeds and executes multi-agent neural fusion to drive macroscopic optimization systems like **CARINA**.

## Technical Guides Index

| Document | Scope & Focus | Key Topics |
|---|---|---|
| 📖 **[System Architecture](architecture.md)** | Core Architecture Specification | Domain-Driven Design (DDD), Clean Architecture, Hexagonal facade patterns, and multi-agent coordination pipeline. |
| 🗂️ **[Domain Entities & Schemas](domain_entities.md)** | Data Topology & States | `MapNode`, `MapEdge`, `DataSource`, `SourceStatus` state machines, and Bayesian Trust Scores ($0.95$ local, $0.60$ global). |
| 🧠 **[MARKVART™ Neural Stack](neural_models.md)** | Deep Neural Architectures | 10 neural models & deterministic spatial engine: PINO-Traffic (LWR PDE), PI-DeepONet, iTransformer, GATv2 Lite, WaveletAE-OCC, and Qwen3 Jurist. |
| ⏱️ **[ADAGIO™ Execution Phases](execution_phases.md)** | Lifecycle & Runtime Engine | Structured phases: Phase 0 (AutoML Optuna), Phase 1 (Golden Dataset bootstrap), Phase 2 (Online 4-thread runtime), and KSE Dead Reckoning. |
| ⚡ **[Data Ingestion & HFT-Link](data_ingestion_and_hft.md)** | High-Frequency Transport | Sensor adapters (HTTP, MQTT, WebSocket), Protocol Buffers (`synapse_hft.proto`), sub-250ms gRPC stream, and self-healing. |
| 🖥️ **[UI Architecture & IPC](ui_architecture.md)** | Native Desktop Interface | Tauri v2 + React 18, Zero-Port Stdio JSON-RPC IPC, and Zustand reactive state stores. |
| 🛡️ **[Safety, Watchdog & Gating](safety_and_watchdog.md)** | Reliability & Out-of-Process Guard | F.E.N.I.X. watchdog supervisor, memory ceiling enforcement, and multi-tiered fallback gating policy. |
| 🧪 **[Testing & Quality Assurance](testing.md)** | Test Suites & Benchmarking | Pytest test suite, synthetic data generators, HFT streaming mocks, and coverage profiling. |

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
