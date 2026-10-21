<div align="center">

<img src="../assets/synapse-logo.png" alt="SYNAPSE CORE Logo" width="120" />

# SYNAPSE — 技术文档中心（简体中文）
### 智慧城市智能感知网关、神经网络融合引擎与高频控制中枢
*Noxfort Systems — A State Of Art Company*

[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat&logo=github)](https://github.com/Noxfort-Systems-Brazil/SYNAPSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)](https://python.org/)
[![Rust](https://img.shields.io/badge/Rust-1.75%2B-DEA584?style=flat&logo=rust&logoColor=white)](https://rust-lang.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0%2B-EE4C2C?style=flat&logo=pytorch&logoColor=white)](https://pytorch.org/)

---

🌐 **语言选择:** **[🇺🇸 English](../en/README.md)** • **[🇧🇷 Português](../pt-br/README.md)** • **[🇪🇸 Español](../es/README.md)** • **[🇫🇷 Français](../fr/README.md)** • **[🇷🇺 Русский](../ru/README.md)** • **[🇨🇳 简体中文](README.md)** • **[📚 文档总中心](../README.md)**

---

</div>

## 欢迎查阅官方中文技术规范库

本目录汇集了 **SYNAPSE CORE**（智慧城市智能感知与神经网络融合网关系统）的完整中文技术文档体系。SYNAPSE 负责接入城市各类型异步传感器数据流，运用多智能体神经网络协同融合算法，向下游 **CARINA** 自适应信号控制机持续输出高精度宏观交通状态张量。

## 专业技术指南索引

| 文档名称 | 核心领域 | 主要内容 |
|---|---|---|
| 📖 **[系统架构核心蓝图](architecture.md)** | 总体架构规范 | 领域驱动设计 (DDD)、整洁架构 (Clean Architecture)、零网络端口 Stdio IPC 与多智能体流水线。 |
| 🗂️ **[领域实体与拓扑模式](domain_entities.md)** | 数据拓扑与状态机 | `MapNode`、`MapEdge`、`DataSource`、`SourceStatus` 零信任状态机与贝叶斯先验可信权重。 |
| 🧠 **[MARKVART™ 神经网络群](neural_models.md)** | 深度神经网络体系 | 10 个深度模型与确定性地图匹配引擎：PINO-Traffic (LWR 偏微分方程)、PI-DeepONet、iTransformer、GATv2 Lite 及 Qwen3 Jurist。 |
| ⏱️ **[ADAGIO™ 执行阶段](execution_phases.md)** | 生命周期与执行引擎 | 结构化三阶段：阶段 0 (Optuna 自动化调参)、阶段 1 (黄金数据集引导)、阶段 2 (四线程并发在线运行时) 与 KSE 航位推算。 |
| ⚡ **[数据采集与 HFT-Link 传输](data_ingestion_and_hft.md)** | 高频数据流传输 | 多协议传感器接入适配器、Protocol Buffers (`synapse_hft.proto`)、亚 250 毫秒 gRPC 流与自愈机制。 |
| 🖥️ **[桌面界面与 IPC 架构](ui_architecture.md)** | 原生桌面交互架构 | Tauri v2 + React 18、无开放端口 Stdio JSON-RPC 通信与 Zustand 响应式状态管理。 |
| 🛡️ **[安全机制与看门狗守卫](safety_and_watchdog.md)** | 高可用与故障平滑降级 | F.E.N.I.X. 独立外部进程看门狗、内存上限熔断防护与分级降级门控策略 (Gating Policy)。 |
| 🧪 **[测试规范与质量保证](testing.md)** | 自动化测试与验证 | Pytest 全覆盖测试套件、合成交通流生成器、gRPC 模拟桩与性能基准测试。 |

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
