# 🖥️ SYNAPSE: Arquitectura UI e IPC Stdio Zero-Port

Este documento expone la arquitectura de la aplicación de escritorio SYNAPSE, detallando el anfitrión nativo en Rust con Tauri v2, la interfaz React 18, el manejo de estados con Zustand y el canal seguro IPC Stdio JSON-RPC sin puertos abiertos.

⬅️ [Centro de Documentación](README.md) | ⚡ [Ingestión y HFT](data_ingestion_and_hft.md) | 🛡️ [Seguridad y Watchdog](safety_and_watchdog.md)

---

## 1. Visión General y Seguridad Zero-Port

Para satisfacer los requisitos de ciberseguridad en centros de control de tráfico, SYNAPSE no abre puertos de red en `localhost`. La comunicación entre la interfaz de escritorio y el núcleo Python opera mediante pipes estándar del sistema operativo con tramas JSON-RPC delimitadas por salto de línea:

```
┌────────────────────────────────────────────────────────┐
│               APLICACIÓN DE ESCRITORIO TAURI v2        │
│                                                        │
│   ┌────────────────────────────────────────────────┐   │
│   │                 REACT 18 SPA                   │   │
│   │  - Tiendas Reactivas Zustand                   │   │
│   │  - Tailwind CSS + Iconos Lucide                │   │
│   │  - Gráficos en Tiempo Real con ECharts         │   │
│   └───────────────────────┬────────────────────────┘   │
│                           │ Comandos Invoke de Tauri   │
│   ┌───────────────────────▼────────────────────────┐   │
│   │               RUST CORE (src-tauri)            │   │
│   │  - Administrador de Procesos Hijos (Python)    │   │
│   │  - Interceptor Asíncrono de Pipes Stdio        │   │
│   └───────────────────────┬────────────────────────┘   │
└───────────────────────────┼────────────────────────────┘
                            │ STDIN / STDOUT (JSON-RPC)
┌───────────────────────────▼────────────────────────────┐
│              BACKEND PYTHON (StdioDaemon)              │
│  - CommandRouter, IpcEventBridge, Motor PyTorch        │
└────────────────────────────────────────────────────────┘
```

---

## 2. Gestión de Estados Frontend (Zustand Stores)

La interfaz se estructura sobre tiendas modulares **Zustand**:

- **`useSensorsStore`**: Registra sensores activos, cadencia de paquetes, índices Bayesianos de confianza y estados (`ACTIVE`, `QUARANTINE`, `FALLBACK`).
- **`useTopologyStore`**: Administra el grafo vial ($V, E$), geocodificación y capacidad de tramos.
- **`useSystemStore`**: Supervisa carga de CPU/GPU, VRAM, latencia de inferencia ($< 15\text{ ms}$) y estado de F.E.N.I.X.
- **`useXaiStore`**: Almacena justificaciones generadas por Qwen3 Jurist y alertas viales.

---

## 3. Protocolo IPC Stdio JSON-RPC

El intercambio asíncrono implementa la especificación JSON-RPC 2.0:

### Ejemplo de Solicitud (UI $\rightarrow$ Python):
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

### Ejemplo de Notificación (Python $\rightarrow$ UI vía STDOUT):
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
