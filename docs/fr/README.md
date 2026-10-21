<div align="center">

<img src="../assets/synapse-logo.png" alt="SYNAPSE CORE Logo" width="120" />

# SYNAPSE — Suite de Documentation Technique (Français)
### Architecture Système, Fusion Neuronale et Perception pour Villes Intelligentes
*Noxfort Systems — A State Of Art Company*

[![Status](https://img.shields.io/badge/Status-Actif-brightgreen?style=flat&logo=github)](https://github.com/Noxfort-Systems-Brazil/SYNAPSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)](https://python.org/)
[![Rust](https://img.shields.io/badge/Rust-1.75%2B-DEA584?style=flat&logo=rust&logoColor=white)](https://rust-lang.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-EE4C2C?style=flat&logo=pytorch&logoColor=white)](https://pytorch.org/)

---

🌐 **Langues:** **[🇺🇸 English](../en/README.md)** • **[🇧🇷 Português](../pt-br/README.md)** • **[🇪🇸 Español](../es/README.md)** • **[🇫🇷 Français](README.md)** • **[🇷🇺 Русский](../ru/README.md)** • **[🇨🇳 简体中文](../zh/README.md)** • **[📚 Hub Central](../README.md)**

---

</div>

## Bienvenue dans la Documentation Officielle en Français

Ce répertoire rassemble l'ensemble de la documentation technique en **Français** pour **SYNAPSE CORE** (Intelligent Perception & Neural Fusion Gateway for Smart City Traffic Management). SYNAPSE traite les flux asynchrones des capteurs urbains et orchestre une fusion neuronale multi-agents afin d'alimenter les systèmes de régulation de feux comme **CARINA**.

## Répertoire des Guides Techniques

| Document | Périmètre et Thématique | Sujets Principaux |
|---|---|---|
| 📖 **[Architecture Système](architecture.md)** | Spécification de l'Architecture | Domain-Driven Design (DDD), Clean Architecture, façades hexagonales et pipeline multi-agents. |
| 🗂️ **[Entités de Domaine et Schémas](domain_entities.md)** | Topologie des Données et États | `MapNode`, `MapEdge`, `DataSource`, automates `SourceStatus` et scores Bayésiens ($0.95$ local, $0.60$ global). |
| 🧠 **[Stack Neuronal MARKVART™](neural_models.md)** | Réseaux de Neurones Profonds | 10 modèles et moteur de map-matching déterministe : PINO-Traffic (EDP LWR), PI-DeepONet, iTransformer, GATv2 Lite, WaveletAE-OCC et Qwen3 Jurist. |
| ⏱️ **[Phases d'Exécution ADAGIO™](execution_phases.md)** | Cycle de Vie et Moteur Runtime | Phases structurées : Phase 0 (AutoML Optuna), Phase 1 (Bootstrap Dataset Doré), Phase 2 (Runtime 4-Thread) et KSE. |
| ⚡ **[Ingestion et HFT-Link](data_ingestion_and_hft.md)** | Transport Haute Fréquence | Adaptateurs capteurs (HTTP, MQTT, WebSocket), Protocol Buffers (`synapse_hft.proto`), flux gRPC sub-250ms et auto-résilience. |
| 🖥️ **[Architecture UI et IPC](ui_architecture.md)** | Interface Desktop Native | Tauri v2 + React 18, IPC Zero-Port Stdio JSON-RPC et gestion d'état réactive avec Zustand. |
| 🛡️ **[Sécurité, Watchdog et Gating](safety_and_watchdog.md)** | Fiabilité et Superviseur | Superviseur hors-processus F.E.N.I.X., plafonnement mémoire et politique de repli (Gating Policy). |
| 🧪 **[Directives de Test et Assurance Qualité](testing.md)** | Tests et Évaluation | Suite Pytest, générateurs de trafic synthétique, simulateurs gRPC et profilage de couverture. |

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
