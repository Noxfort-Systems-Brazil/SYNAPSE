# 05. Data Ingestion & HFT Network

> **Heterogeneous Sensor Ingestion, Protocol Buffers v3, Sub-250ms gRPC Streaming, and Auto-Recovery Self-Healing**

---

> 🧭 **Navigation**:
> [🏠 Synapse Core](../README.md) • [📚 Docs Index](README.md) • [« Previous: 04. Execution Phases](04_execution_phases.md) • [Next: 06. Developer Guide »](06_developer_guide.md)

---

## 🌐 Overview

The I/O boundary of SYNAPSE is structured into two core responsibilities:
1. **Ingestion Pipeline ([`src/adapters/`](../src/README.md#subsystem-directory-breakdown))**: Asynchronously ingesting heterogeneous municipal telemetry (inductive loops, cameras, radars, Waze/TomTom cloud APIs).
2. **High-Frequency Transport Link (HFT-Link)**: Streaming fluid-dynamically validated present-state matrices to downstream macroscopic traffic signal controllers ([CARINA](https://github.com/noxfort/carina)) via high-throughput HTTP/2 gRPC.

```text
  [Field Sensors & APIs]
  Inductive Loops, Cameras, Radars, Waze, TomTom
            │  (HTTP Push/Poll, MQTT Stream, WebSocket)
            ▼
  ┌──────────────────────────────────────────────────┐
  │     src/adapters/ (IngestionHub & Adapters)      │
  │     - Schema normalizers & zero-trust buffer     │
  └─────────────────────────┬────────────────────────┘
                            │ Raw Datagrams
                            ▼
  ┌──────────────────────────────────────────────────┐
  │         Zero-Trust Ingestion Gatekeeper          │
  │     - DistilRoBERTa + Symbolic Physical Bounds   │
  └─────────────────────────┬────────────────────────┘
                            │ Validated MapNode State
                            ▼
  ┌──────────────────────────────────────────────────┐
  │       MARKVART™ Neural Continuum Pipeline        │
  │     - iTransformer + PINO + GATv2                │
  └─────────────────────────┬────────────────────────┘
                            │ Fused Traffic Snapshot
                            ▼
  ┌──────────────────────────────────────────────────┐
  │        HFT-Link gRPC Client (HTTP/2 Stream)      │
  │     - proto/synapse_hft.proto (< 250ms Latency)  │
  └─────────────────────────┬────────────────────────┘
                            │ Binary Protocol Buffers
                            ▼
               [CARINA Traffic Controller]
```

---

## 📥 1. The Ingestion Pipeline

### Modular Adapters (`src/adapters/`)
Sensor protocols subclass `BaseAdapter` (`src/interfaces/`):
- **`HttpPollingAdapter`**: Periodically fetches REST API endpoints (e.g. municipal open-data portals, TomTom congestion APIs).
- **`HttpPushAdapter`**: Lightweight micro-server receiving webhook pushes from smart city cameras and ANPR systems.
- **`MqttAdapter`**: Subscribes to urban IoT broker topics (e.g., `city/sensors/+/telemetry`).
- **`WebSocketAdapter`**: Continuous full-duplex socket for high-rate radar sensors.
- **`HistoricalReplayAdapter`**: Reads chronological Parquet logs for deterministic stress tests and validation.

### Database Persistence (`src/infrastructure/postgres_manager.py`)
- Continuously dumps approved telemetry records into compressed columnar `.parquet` files partitioned by date (`year=YYYY/month=MM/day=DD/`).
- Supplies the [Phase 1 Bootstrap](04_execution_phases.md#phase-1-offline-bootstrap-bootstrap_phasepy) engine with historical Golden Datasets.

---

## ⚡ 2. The HFT-Link (High-Frequency Transport)

Located in [`src/infrastructure/grpc_connector.py`](../src/infrastructure/grpc_connector.py) and [`src/infrastructure/hft_grpc_client.py`](../src/infrastructure/hft_grpc_client.py), the HFT-Link guarantees uninterrupted, low-jitter perception delivery to CARINA.

### Channel Configuration & Performance Tuning
Because urban networks can comprise tens of thousands of intersections and road edges:
- **Maximum Message Size**: Set to **50 MB** (`50 * 1024 * 1024` bytes) for both transmission and reception to support uncompressed city-scale SUMO graphs:
  ```python
  ('grpc.max_send_message_length', 50 * 1024 * 1024),
  ('grpc.max_receive_message_length', 50 * 1024 * 1024),
  ```
- **KeepAlive Configuration**:
  - `keepalive_time_ms = 10000` (10s periodic heartbeats).
  - `keepalive_timeout_ms = 5000` (5s timeout before considering channel dead).
  - `http2.max_pings_without_data = 0` (Continuous keepalives even during quiet periods).

---

## 🔄 3. The 4-Stage Transmission Lifecycle

```mermaid
sequenceDiagram
    autonumber
    participant S as SYNAPSE Core
    participant C as CARINA Controller

    Note over S,C: Stage 1: Handshake
    S->>C: Ping(Empty)
    C-->>S: SystemState(active=true, server_time=...)

    Note over S,C: Stage 2: Topology Synchronization
    S->>C: LoadScenario(ScenarioDefinition)
    Note right of C: Unpacks SUMO nodes, edges, signal groups
    C-->>S: ScenarioStatus(accepted=true, map_hash=...)

    Note over S,C: Stage 3: Operational Arming
    S->>C: SystemControl(action=START)
    C-->>S: CommandResponse(status=OK)

    Note over S,C: Stage 4: High-Frequency Perception Stream
    loop Continuous Cycle (1.0s or 0.1s)
        S->>C: StreamTraffic(TrafficFrame)
    end
```

1. **Stage 1: Handshake (`Ping`)**: Verifies controller liveness and synchronizes high-precision UNIX timestamps.
2. **Stage 2: Scenario Upload (`LoadScenario`)**: Transmits the topological graph, compressed SUMO `.net.xml` geometry, and peak-hour schedule clusters.
3. **Stage 3: Operational Control (`SystemControl`)**: Transitions downstream controller states (`START`, `PAUSE`, `STOP`, `RESET`).
4. **Stage 4: Client-Streaming (`StreamTraffic`)**: Streams continuous `TrafficFrame` messages containing occupancy, mean velocity, and estimated queue lengths per edge.

---

## 🛡️ 4. Auto-Recovery Self-Healing Loop

In hostile physical networking conditions, edge links drop. SYNAPSE implements an automated self-healing loop in [`src/infrastructure/hft_recovery.py`](../src/infrastructure/hft_recovery.py):

1. **In-Memory Scenario Caching**: During Stage 2, SYNAPSE caches the serialized scenario binary payload (`_recovery_payload`).
2. **Exception Interception**: If gRPC raises `grpc.StatusCode.UNAVAILABLE` or `BrokenPipeError`, the core thread **does not abort**.
3. **Non-Blocking Reconnection Loop**: A background recovery thread attempts exponential backoff pings to CARINA.
4. **Transparent Re-Arming**: The instant the connection returns, SYNAPSE:
   - Re-executes `LoadScenario()` with the cached binary payload.
   - Issues `SystemControl(action=START)`.
   - Seamlessly resumes `StreamTraffic()` without dropping active sensor state or restarting PyTorch models.

---

> 🧭 **Next Chapter**: Set up developer tools and compile Protobufs in [06. Developer Guide](06_developer_guide.md).

---

<p align="center">
  <sub>SYNAPSE Ingestion & Transport — Noxfort Systems</sub><br/>
  <sub><a href="#05-data-ingestion--hft-network">Back to top ↑</a></sub>
</p>
