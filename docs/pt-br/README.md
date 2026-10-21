<div align="center">

<img src="../assets/synapse-logo.png" alt="SYNAPSE CORE Logo" width="120" />

# SYNAPSE — Suíte de Documentação Técnica (Português do Brasil)
### Arquitetura de Sistemas, Fusão Neural e Percepção em Cidades Inteligentes
*Noxfort Systems — A State Of Art Company*

[![Status](https://img.shields.io/badge/Status-Ativo-brightgreen?style=flat&logo=github)](https://github.com/Noxfort-Systems-Brazil/SYNAPSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)](https://python.org/)
[![Rust](https://img.shields.io/badge/Rust-1.75%2B-DEA584?style=flat&logo=rust&logoColor=white)](https://rust-lang.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-EE4C2C?style=flat&logo=pytorch&logoColor=white)](https://pytorch.org/)

---

🌐 **Idiomas:** **[🇺🇸 English](../en/README.md)** • **[🇧🇷 Português (Brasil)](README.md)** • **[🇪🇸 Español](../es/README.md)** • **[🇫🇷 Français](../fr/README.md)** • **[🇷🇺 Русский](../ru/README.md)** • **[🇨🇳 简体中文](../zh/README.md)** • **[📚 Central de Documentação](../README.md)**

---

</div>

## Bem-vindo à Documentação Oficial em Português

Este diretório reúne toda a suíte de documentação técnica em **Português do Brasil** do ecossistema **SYNAPSE CORE** (Intelligent Perception & Neural Fusion Gateway for Smart City Traffic Management). O SYNAPSE processa fluxos sensoriais municipais assíncronos e executa fusão neural multiagente para alimentar sistemas semafóricos adaptativos como o **CARINA**.

## Índice de Guias Especializados

| Documento | Tema & Escopo | Principais Tópicos |
|---|---|---|
| 📖 **[Arquitetura do Sistema](architecture.md)** | Especificação Arquitetural | Domain-Driven Design (DDD), Clean Architecture, padrões de fachada hexagonal e pipeline multiagente. |
| 🗂️ **[Entidades de Domínio e Esquemas](domain_entities.md)** | Topologia de Dados e Estados | `MapNode`, `MapEdge`, `DataSource`, máquinas de estado `SourceStatus` e Trust Scores Bayesianos ($0,95$ local, $0,60$ global). |
| 🧠 **[Stack Neural MARKVART™](neural_models.md)** | Redes Neurais Profundas | 10 modelos neurais e motor de map-matching determinístico: PINO-Traffic (EDP LWR), PI-DeepONet, iTransformer, GATv2 Lite, WaveletAE-OCC e Qwen3 Jurist. |
| ⏱️ **[Fases de Execução ADAGIO™](execution_phases.md)** | Ciclo de Vida e Runtime | Fases estruturadas: Fase 0 (AutoML Optuna), Fase 1 (Bootstrap Dataset Dourado), Fase 2 (Runtime 4-Thread) e KSE Dead Reckoning. |
| ⚡ **[Ingestão de Dados e HFT-Link](data_ingestion_and_hft.md)** | Transporte de Alta Frequência | Adaptadores sensoriais (HTTP, MQTT, WebSocket), Protocol Buffers (`synapse_hft.proto`), streaming gRPC sub-250ms e auto-recuperação. |
| 🖥️ **[Arquitetura UI e IPC](ui_architecture.md)** | Interface Desktop Nativa | Tauri v2 + React 18, IPC Zero-Port Stdio JSON-RPC e gerenciamento reativo com Zustand. |
| 🛡️ **[Segurança, Watchdog e Gating](safety_and_watchdog.md)** | Confiabilidade e Supervisor | Supervisor out-of-process F.E.N.I.X., teto de memória e política de degradação suave (Gating Policy). |
| 🧪 **[Diretrizes de Testes e QA](testing.md)** | Testes e Benchmarks | Suíte Pytest, geradores de dados sintéticos, mocks determinísticos e perfilamento de cobertura. |

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
