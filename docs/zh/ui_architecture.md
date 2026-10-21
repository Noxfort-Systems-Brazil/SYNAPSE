# 🖥️ SYNAPSE: 桌面前端交互架构与零端口 Stdio IPC

本规范定义 SYNAPSE 桌面端系统的技术架构：基于 Tauri v2 的 Rust 原生外壳、React 18 前端交互层、Zustand 响应式全局状态树以及无网络开放端口的标准输入输出 (Stdio) JSON-RPC 桥接协议。

⬅️ [文档总中心](README.md) | ⚡ [数据采集与 HFT](data_ingestion_and_hft.md) | 🛡️ [安全机制与守卫](safety_and_watchdog.md)

---

## 1. 架构总览与零端口 (Zero-Port) 安全机制

为满足智能交通指挥中心严苛的网络隔离与安全准入标准，SYNAPSE 在本机运行时完全不开放任何 HTTP 或 WebSocket 网络监听端口。前端桌面应用通过操作系统管道以换行符分隔的 JSON-RPC 报文与 Python 内核通信：

```
┌────────────────────────────────────────────────────────┐
│                   TAURI v2 桌面宿主环境                │
│                                                        │
│   ┌────────────────────────────────────────────────┐   │
│   │                 REACT 18 SPA                   │   │
│   │  - Zustand 响应式全局状态树                    │   │
│   │  - Tailwind CSS + Lucide 矢量图标库            │   │
│   │  - 基于 ECharts 的实时动态遥测大屏             │   │
│   └───────────────────────┬────────────────────────┘   │
│                           │ Tauri Invoke 指令通道      │
│   ┌───────────────────────▼────────────────────────┐   │
│   │               RUST 核心 (src-tauri)            │   │
│   │  - 子进程生命周期守护 (拉起 Python 引擎)       │   │
│   │  - 异步非阻塞 Stdio 管道报文拦截器             │   │
│   └───────────────────────┬────────────────────────┘   │
└───────────────────────────┼────────────────────────────┘
                            │ 标准输入输出 STDIN/STDOUT (JSON-RPC)
┌───────────────────────────▼────────────────────────────┐
│              PYTHON 后端引擎 (StdioDaemon)             │
│  - CommandRouter, IpcEventBridge, PyTorch 计算循环     │
└────────────────────────────────────────────────────────┘
```

---

## 2. 前端状态管理 (Zustand Stores)

前端界面采用解耦的 **Zustand** 状态库进行响应式管理：

- **`useSensorsStore`**：管理活跃感知设备列表、数据帧率、贝叶斯可信分及状态标记 (`ACTIVE`, `QUARANTINE`, `FALLBACK`)。
- **`useTopologyStore`**：加载路网拓扑图 ($V, E$)、路段经纬度多边形与车道通行能力。
- **`useSystemStore`**：实时监控主机 CPU/GPU 使用率、显存消耗、推理周期时延 ($< 15\text{ ms}$) 与 F.E.N.I.X. 状态。
- **`useXaiStore`**：展示 Qwen3 Jurist 大模型生成的事件成因解释及可信度溯源证据。

---

## 3. Stdio JSON-RPC 2.0 通信协议

前后端通过纯异步 JSON-RPC 2.0 格式传递控制信令与事件：

### 请求报文样例 (UI $\rightarrow$ Python)：
```json
{
  "jsonrpc": "2.0",
  "id": "req-1042",
  "method": "get_topology_snapshot",
  "params": {
    "include_metrics": true
  }
}
```

### 事件推送样例 (Python $\rightarrow$ UI via STDOUT)：
```json
{
  "jsonrpc": "2.0",
  "method": "on_telemetry_tick",
  "params": {
    "timestamp_ns": 1774728190000000,
    "active_sensors": 48,
    "mean_trust_score": 0.942,
    "hft_latency_ms": 1.2
  }
}
```

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
