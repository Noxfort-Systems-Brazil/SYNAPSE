# 🖥️ SYNAPSE: Архитектура UI и бессерверный IPC Stdio

Данный документ описывает архитектуру десктопного интерфейса SYNAPSE: нативный хост на Rust (Tauri v2), фронтенд на React 18, реактивные хранилища Zustand и протокол IPC Stdio JSON-RPC без открытия сетевых портов.

⬅️ [Главный Хаб](README.md) | ⚡ [Сбор данных и HFT](data_ingestion_and_hft.md) | 🛡️ [Безопасность и Watchdog](safety_and_watchdog.md)

---

## 1. Концепция и безопасность Zero-Port

В соответствии с требованиями безопасности диспетчерских пунктов управления движением, SYNAPSE не открывает сетевые порты на `localhost`. Взаимодействие фронтенда и Python-бэкенда происходит через стандартные анонимные каналы ОС с использованием JSON-RPC:

```
┌────────────────────────────────────────────────────────┐
│             ДЕСКТОПНОЕ ПРИЛОЖЕНИЕ TAURI v2             │
│                                                        │
│   ┌────────────────────────────────────────────────┐   │
│   │                 REACT 18 SPA                   │   │
│   │  - Реактивные хранилища Zustand                │   │
│   │  - Tailwind CSS + Иконки Lucide                │   │
│   │  - Визуализация в реальном времени ECharts     │   │
│   └───────────────────────┬────────────────────────┘   │
│                           │ Команды Tauri Invoke       │
│   ┌───────────────────────▼────────────────────────┐   │
│   │               RUST CORE (src-tauri)            │   │
│   │  - Менеджер дочерних процессов (Python)        │   │
│   │  - Асинхронный перехватчик каналов Stdio       │   │
│   └───────────────────────┬────────────────────────┘   │
└───────────────────────────┼────────────────────────────┘
                            │ STDIN / STDOUT (JSON-RPC)
┌───────────────────────────▼────────────────────────────┐
│              BACKEND PYTHON (StdioDaemon)              │
│  - CommandRouter, IpcEventBridge, Движок PyTorch       │
└────────────────────────────────────────────────────────┘
```

---

## 2. Управление состоянием (Хранилища Zustand)

Интерфейс построен на модульных хранилищах **Zustand**:

- **`useSensorsStore`**: Учет активных датчиков, частоты пакетов, весов доверия и статусов (`ACTIVE`, `QUARANTINE`, `FALLBACK`).
- **`useTopologyStore`**: Граф дорожной сети ($V, E$), геопривязка и пропускная способность полос.
- **`useSystemStore`**: Нагрузка CPU/GPU, VRAM, время цикла инференса ($< 15\text{ ms}$) и статус F.E.N.I.X.
- **`useXaiStore`**: Текстовые заключения нейросети Qwen3 Jurist и дорожные инциденты.

---

## 3. Протокол IPC Stdio JSON-RPC

Обмен сообщениями следует стандарту JSON-RPC 2.0:

### Пример запроса (Интерфейс $\rightarrow$ Python):
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

### Пример оповещения (Python $\rightarrow$ Интерфейс):
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
