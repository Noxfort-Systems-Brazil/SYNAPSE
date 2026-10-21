# 🖥️ SYNAPSE: UI Architecture & Zero-Port Stdio IPC

This document specifies the frontend architecture of the SYNAPSE desktop application, detailing the Tauri v2 Rust host, React 18 user interface, Zustand reactive state management, and the Zero-Port Stdio JSON-RPC IPC bridge.

⬅️ [Documentation Hub](README.md) | ⚡ [Data Ingestion & HFT](data_ingestion_and_hft.md) | 🛡️ [Safety & Watchdog](safety_and_watchdog.md)

---

## 1. Architectural Overview & Zero-Port Security

To meet municipal security standards in traffic control centers, SYNAPSE avoids exposing local HTTP, REST, or WebSocket ports on localhost. Instead, the desktop UI communicates with the Python core through an OS pipe newline-delimited **Stdio JSON-RPC IPC**:

```
┌────────────────────────────────────────────────────────┐
│                   TAURI v2 DESKTOP APP                 │
│                                                        │
│   ┌────────────────────────────────────────────────┐   │
│   │                 REACT 18 SPA                   │   │
│   │  - Zustand Reactive Stores                     │   │
│   │  - Tailwind CSS + Lucide Icons                 │   │
│   │  - ECharts Real-Time Visualizations            │   │
│   └───────────────────────┬────────────────────────┘   │
│                           │ Tauri Invoke Commands      │
│   ┌───────────────────────▼────────────────────────┐   │
│   │               RUST CORE (src-tauri)            │   │
│   │  - Child Process Manager (Spawns Python Core)  │   │
│   │  - Non-Blocking Async Stdio Pipe Interceptor   │   │
│   └───────────────────────┬────────────────────────┘   │
└───────────────────────────┼────────────────────────────┘
                            │ STDIN / STDOUT (Newline JSON-RPC)
┌───────────────────────────▼────────────────────────────┐
│              PYTHON BACKEND (StdioDaemon)              │
│  - CommandRouter, IpcEventBridge, PyTorch Engine       │
└────────────────────────────────────────────────────────┘
```

---

## 2. Frontend State Management (Zustand Stores)

The user interface uses modular **Zustand** stores for responsive, boilerplate-free state updates:

- **`useSensorsStore`**: Tracks active physical and virtual sensor feeds, packet rates, Bayesian trust scores, and status flags (`ACTIVE`, `QUARANTINE`, `FALLBACK`).
- **`useTopologyStore`**: Manages the loaded roadway graph ($V, E$), geographic node coordinates, and segment capacities.
- **`useSystemStore`**: Tracks CPU/GPU utilization, VRAM usage, inference cycle duration ($< 15\text{ ms}$), and F.E.N.I.X. watchdog status.
- **`useXaiStore`**: Holds Qwen3 Jurist explanations, anomaly alerts, and mathematical formulation breakdowns.

---

## 3. Stdio JSON-RPC IPC Protocol

Commands and telemetry stream asynchronously over standard input and output using JSON-RPC 2.0:

### Sample Request (UI $\rightarrow$ Python Core):
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

### Sample Event (Python Core $\rightarrow$ UI via STDOUT):
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
