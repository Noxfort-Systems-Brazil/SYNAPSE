<div align="center">

<img src="../assets/synapse-logo.png" alt="SYNAPSE CORE Logo" width="120" />

# SYNAPSE — Комплект технической документации (Русский)
### Системная архитектура, нейросетевая конвергенция и восприятие умного города
*Noxfort Systems — A State Of Art Company*

[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat&logo=github)](https://github.com/Noxfort-Systems-Brazil/SYNAPSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)](https://python.org/)
[![Rust](https://img.shields.io/badge/Rust-1.75%2B-DEA584?style=flat&logo=rust&logoColor=white)](https://rust-lang.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-EE4C2C?style=flat&logo=pytorch&logoColor=white)](https://pytorch.org/)

---

🌐 **Языки:** **[🇺🇸 English](../en/README.md)** • **[🇧🇷 Português](../pt-br/README.md)** • **[🇪🇸 Español](../es/README.md)** • **[🇫🇷 Français](../fr/README.md)** • **[🇷🇺 Русский](README.md)** • **[🇨🇳 简体中文](../zh/README.md)** • **[📚 Главный Хаб](../README.md)**

---

</div>

## Добро пожаловать в официальную документацию на русском языке

В данном каталоге собрана полная техническая документация платформы **SYNAPSE CORE** (Intelligent Perception & Neural Fusion Gateway for Smart City Traffic Management). SYNAPSE обрабатывает асинхронные потоки городских датчиков и выполняет мультиагентную нейросетевую агрегацию для передачи данных в адаптивные контроллеры светофоров **CARINA**.

## Каталог технических руководств

| Документ | Направление и область | Ключевые темы |
|---|---|---|
| 📖 **[Архитектура системы](architecture.md)** | Спецификация архитектуры | Предметно-ориентированное проектирование (DDD), Clean Architecture, бессерверный IPC Stdio и мультиагентный пайплайн. |
| 🗂️ **[Сущности домена и схемы](domain_entities.md)** | Топология данных и состояния | `MapNode`, `MapEdge`, `DataSource`, конечные автоматы `SourceStatus` и байесовские веса доверия ($0.95$ локальные, $0.60$ внешние). |
| 🧠 **[Нейросетевой стек MARKVART™](neural_models.md)** | Архитектура глубоких сетей | 10 нейросетей и детерминированный движок map-matching: PINO-Traffic (ДУЧП LWR), PI-DeepONet, iTransformer, GATv2 Lite, WaveletAE-OCC и Qwen3 Jurist. |
| ⏱️ **[Фазы выполнения ADAGIO™](execution_phases.md)** | Жизненный цикл и среда | Структурированные фазы: Фаза 0 (AutoML Optuna), Фаза 1 (Золотой датасет), Фаза 2 (Онлайн 4 потока) и KSE Dead Reckoning. |
| ⚡ **[Сбор данных и HFT-Link](data_ingestion_and_hft.md)** | Высокочастотный транспорт | Адаптеры датчиков (HTTP, MQTT, WebSocket), Protocol Buffers (`synapse_hft.proto`), стриминг gRPC sub-250ms и самовосстановление. |
| 🖥️ **[Архитектура интерфейса и IPC](ui_architecture.md)** | Нативное десктоп-приложение | Tauri v2 + React 18, Zero-Port Stdio JSON-RPC IPC и реактивное управление состоянием с помощью Zustand. |
| 🛡️ **[Безопасность и Watchdog](safety_and_watchdog.md)** | Надежность и супервизор | Внешний супервизор процессов F.E.N.I.X., контроль памяти и ступенчатая политика деградации (Gating Policy). |
| 🧪 **[Тестирование и контроль качества](testing.md)** | Тесты и бенчмарки | Набор Pytest, генераторы синтетического трафика, симуляторы gRPC и профилирование покрытия. |

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
