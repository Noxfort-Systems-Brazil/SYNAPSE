<div align="center">

<img src="../assets/synapse-logo.png" alt="SYNAPSE CORE Logo" width="120" />

# SYNAPSE — Suite de Documentación Técnica (Español)
### Arquitectura de Sistemas, Fusión Neural y Percepción para Ciudades Inteligentes
*Noxfort Systems — A State Of Art Company*

[![Status](https://img.shields.io/badge/Status-Activo-brightgreen?style=flat&logo=github)](https://github.com/Noxfort-Systems-Brazil/SYNAPSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)](https://python.org/)
[![Rust](https://img.shields.io/badge/Rust-1.75%2B-DEA584?style=flat&logo=rust&logoColor=white)](https://rust-lang.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-EE4C2C?style=flat&logo=pytorch&logoColor=white)](https://pytorch.org/)

---

🌐 **Idiomas:** **[🇺🇸 English](../en/README.md)** • **[🇧🇷 Português](../pt-br/README.md)** • **[🇪🇸 Español](README.md)** • **[🇫🇷 Français](../fr/README.md)** • **[🇷🇺 Русский](../ru/README.md)** • **[🇨🇳 简体中文](../zh/README.md)** • **[📚 Centro de Documentación](../README.md)**

---

</div>

## Bienvenido a la Documentación Oficial en Español

Este directorio reúne la suite completa de documentación técnica en **Español** para **SYNAPSE CORE** (Intelligent Perception & Neural Fusion Gateway for Smart City Traffic Management). SYNAPSE procesa flujos sensoriales asíncronos municipales y ejecuta fusión neural multi-agente para alimentar sistemas semafóricos adaptativos como **CARINA**.

## Directorio de Guías Técnicas

| Documento | Alcance y Enfoque | Temas Principales |
|---|---|---|
| 📖 **[Arquitectura del Sistema](architecture.md)** | Especificación Arquitectónica | Domain-Driven Design (DDD), Clean Architecture, patrones de fachada hexagonal y pipeline multi-agente. |
| 🗂️ **[Entidades de Dominio y Esquemas](domain_entities.md)** | Topología de Datos y Estados | `MapNode`, `MapEdge`, `DataSource`, máquinas de estado `SourceStatus` y puntuaciones Bayesianas ($0.95$ local, $0.60$ global). |
| 🧠 **[Stack Neural MARKVART™](neural_models.md)** | Redes Neuronales Profundas | 10 modelos neuronales y motor determinista de map-matching: PINO-Traffic (EDP LWR), PI-DeepONet, iTransformer, GATv2 Lite, WaveletAE-OCC y Qwen3 Jurist. |
| ⏱️ **[Fases de Ejecución ADAGIO™](execution_phases.md)** | Ciclo de Vida y Motor Runtime | Fases estructuradas: Fase 0 (AutoML Optuna), Fase 1 (Bootstrap Golden Dataset), Fase 2 (Runtime 4-Thread) y KSE Dead Reckoning. |
| ⚡ **[Ingestión de Datos y HFT-Link](data_ingestion_and_hft.md)** | Transporte de Alta Frecuencia | Adaptadores sensoriales (HTTP, MQTT, WebSocket), Protocol Buffers (`synapse_hft.proto`), streaming gRPC sub-250ms y auto-recuperación. |
| 🖥️ **[Arquitectura UI e IPC](ui_architecture.md)** | Interfaz de Escritorio Nativa | Tauri v2 + React 18, IPC Zero-Port Stdio JSON-RPC y gestión reactiva con Zustand. |
| 🛡️ **[Seguridad, Watchdog y Gating](safety_and_watchdog.md)** | Confiabilidad y Supervisor | Supervisor out-of-process F.E.N.I.X., límite de memoria y política de degradación escalonada (Gating Policy). |
| 🧪 **[Pruebas y Control de Calidad](testing.md)** | Pruebas y Benchmarks | Suite Pytest, generadores de datos sintéticos, mocks deterministas y verificación de cobertura. |

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
