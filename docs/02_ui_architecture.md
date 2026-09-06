# 02. UI Architecture & Modern Desktop Frontend (Tauri v2 + React 18)

> **High-Performance Native Desktop Interface, Rust Sidecar Manager, Zero-Port Stdio IPC, and Reactive State**

---

> 🧭 **Navigation**:
> [🏠 Synapse Core](../README.md) • [📚 Docs Index](README.md) • [« Previous: 01. Domain Entities](01_domain_entities.md) • [Next: 03. Neural Models »](03_neural_models.md)

---

## 🖥️ Overview

The SYNAPSE desktop client is an enterprise-grade operator workstation located in the [`ui/`](../ui/README.md) directory. It is engineered with **Tauri v2**, **React 18**, **TypeScript 5**, **Zustand 4**, and **Tailwind CSS 3**.

The client provides municipal traffic control engineers with sub-second visual inspection of the city road grid, real-time telemetry from the 11 MARKVART™ models, XAI audit legal reports, and zero-trust sensor diagnostics.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        TAURI v2 DESKTOP HOST                           │
│                                                                        │
│   ┌──────────────────────────────────────────────────────────────┐     │
│   │                 REACT 18 WEBVIEW (ui/src_ui/)                │     │
│   │  - Zustand Stores: useSensorsStore, useTopologyStore, etc.   │     │
│   │  - SumoMapCanvas: WebGL/Canvas road topology visualizer      │     │
│   │  - LiveDashboard: ECharts telemetry at 60 FPS                │     │
│   │  - XaiInspector: KaTeX mathematical formulas & legal audits  │     │
│   └──────────────────────────────┬───────────────────────────────┘     │
│                                  │ Tauri Invoke / Event Bridge         │
│   ┌──────────────────────────────▼───────────────────────────────┐     │
│   │                  RUST BACKEND (ui/src-tauri/)                │     │
│   │  - Sidecar Process Manager & Window Constraints              │     │
│   │  - Non-blocking Piped Stdio Interceptor (Zero Network Ports) │     │
│   └──────────────────────────────┬───────────────────────────────┘     │
└──────────────────────────────────┼─────────────────────────────────────┘
                                   │ STDIN / STDOUT (JSON-RPC)
┌──────────────────────────────────▼─────────────────────────────────────┐
│                    PYTHON CORE (src/ipc/stdio_daemon.py)               │
│  - AppState, IngestionHub, MARKVART Neural Inference, HFT-Link Stream  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Structure & Key Components (`ui/src_ui/`)

The frontend is structured in [`ui/src_ui/`](../ui/README.md#📂-frontend-directory-structure):

1. **`Header`** (`ui/src_ui/components/layout/Header.tsx`):
   - Real-time operating phase badges ([Phase 0, 1, 2](04_execution_phases.md)).
   - IPC heartbeat indicator with live round-trip latency.
   - Dynamic language selector (`pt_BR` / `en_US`) and Dark/Light theme toggles.
2. **`Sidebar`** (`ui/src_ui/components/layout/Sidebar.tsx`):
   - Operational phase switcher (Optimization, Bootstrap, Runtime).
   - Sensor inventory categorized by [State](01_domain_entities.md#sourcestatus-state-machine) (`QUARANTINE`, `ACTIVE`, `FALLBACK`).
   - Local vs Global sensor filtering.
3. **`SumoMapCanvas`** (`ui/src_ui/components/map/SumoMapCanvas.tsx`):
   - Hardware-accelerated 2D Canvas/WebGL road network visualizer.
   - Renders SUMO `.net.xml` nodes and edges with traffic-light signal heads.
   - Smooth viewport pan, zoom, edge selection, and velocity heatmaps.
4. **`LiveDashboard`** (`ui/src_ui/components/dashboard/LiveDashboard.tsx`):
   - Real-time streaming charts powered by **Apache ECharts 5**.
   - Graphs velocity distribution, edge occupancy, queue lengths, and packet throughput.
5. **`XaiInspector`** (`ui/src_ui/components/xai/XaiInspector.tsx`):
   - Explainable AI & Safety Auditor panel rendering legal verdicts from the Qwen3 Jurist Agent.
   - Renders **KaTeX** mathematical derivations justifying signal timing modifications.
6. **`LogConsole`** (`ui/src_ui/components/layout/LogConsole.tsx`):
   - Retractable terminal drawer displaying real-time system logs with severity filtering (`INFO`, `WARN`, `ERROR`, `CRITICAL`).

---

## ⚡ Zero-Port IPC Bridge (`Piped STDIO`)

To guarantee absolute network isolation in secure traffic control facilities, SYNAPSE completely eliminates local TCP ports (such as `localhost:8000` or WebSockets) between the frontend and backend:

1. **Rust Sidecar (`ui/src-tauri/`)**:
   - Spawns the Python core as a background child process:
     ```bash
     python synapse.py --daemon
     ```
   - Connects directly to the child's `sys.stdin` and `sys.stdout` file descriptors.
2. **Asynchronous Streaming (Python $\rightarrow$ React)**:
   - PyTorch inference cycles emit telemetry frames as newline-delimited JSON envelopes:
     ```json
     {"type": "event", "event": "telemetry_tick", "payload": {"fps": 59.8, "cycle_ms": 16.4, "active_sensors": 48}}
     ```
   - Rust intercepts `stdout`, deserializes the line, and emits a Tauri window event:
     ```rust
     app_handle.emit("synapse:telemetry_tick", payload)?;
     ```
3. **Command Dispatching (React $\rightarrow$ Python)**:
   - React dispatches user actions via Tauri invoke:
     ```typescript
     await invoke('send_synapse_command', { action: 'start_system', payload: {} });
     ```
   - Rust formats the command into JSON and writes directly to Python's `stdin`.

---

## 🗄️ State Management (Zustand Reactive Stores)

All UI state is decoupled into modular Zustand stores in `ui/src_ui/stores/`:

| Store | File | Primary Responsibility |
| :--- | :--- | :--- |
| **`useBridgeManager`** | `useBridgeManager.ts` | IPC connection state, heartbeat listener, and RPC dispatching. |
| **`useSensorsStore`** | `useSensorsStore.ts` | Real-time sensor catalog, trust scores, and telemetry buffers. |
| **`useTopologyStore`** | `useTopologyStore.ts` | Road network geometry (`MapNode`, `MapEdge`), viewport zoom/pan. |
| **`useSystemStore`** | `useSystemStore.ts` | Operating phase state machine, cycle latency, CPU/VRAM usage. |
| **`useXaiStore`** | `useXaiStore.ts` | Jurist agent explanations, anomaly alerts, KaTeX proofs. |
| **`useReportStore`** | `useReportStore.ts` | Exportable PDF / DOCX compliance and audit report generation. |
| **`useMunicipalSettingsStore`** | `useMunicipalSettingsStore.ts` | Urban speed limits, yellow clearance intervals, and thresholds. |

---

## 🌐 Internationalization (i18n)

Localization is handled via `i18next` with structured JSON locale dictionaries:
- `ui/src_ui/i18n/locales/pt_BR.json` — Brazilian Portuguese (Default municipal language)
- `ui/src_ui/i18n/locales/en_US.json` — American English

Language changes trigger an immediate DOM update across all Zustand stores without requiring application restarts.

---

> 🧭 **Next Chapter**: Discover the mathematical formulation of the 11 deep neural architectures in [03. Neural Models & PyTorch Implementations](03_neural_models.md).

---

<p align="center">
  <sub>SYNAPSE UI Documentation — Noxfort Systems</sub><br/>
  <sub><a href="#02-ui-architecture--modern-desktop-frontend-tauri-v2--react-18">Back to top ↑</a></sub>
</p>
