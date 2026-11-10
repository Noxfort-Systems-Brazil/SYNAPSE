# ⚡ SYNAPSE: Data Ingestion & HFT-Link gRPC Transport

This document details the multi-protocol sensory ingestion pipeline, Protocol Buffers v3 specifications, high-frequency gRPC streaming architecture, and self-healing connection recovery loops.

⬅️ [Documentation Hub](README.md) | ⏱️ [Execution Phases](execution_phases.md) | 🖥️ [Desktop UI](ui_architecture.md)

---

## 1. Heterogeneous Ingestion Hub

The Ingestion Hub (`src/adapters/ingestion_hub.py` and `src/engine/ingestion_pipeline.py`) operates multi-protocol adapters designed to normalize asynchronous sensory streams:

- **HTTP Ingestion**: REST endpoints accepting JSON payloads from legacy city management systems and cloud providers (Waze CCP, TomTom Move).
- **MQTT Broker Client**: Subscribes to telemetry topics published by connected road-side units (RSUs) and induction loop controllers (`traffic/sensors/#`).
- **WebSocket Gateway**: Full-duplex persistent connections for live radar tracking feeds.
- **High-Performance Go Gateway**: Compiled CGO-free binary (`synapse-go`) handling raw socket packet reception at line rate without Python interpreter overhead.
- **Canonical Device Alias Resolution (`device_id_map`)**: Automatically resolves hardware aliases embedded in sensor payloads (e.g., `loop_01` $\rightarrow$ `src_2`) across `IngestionPipeline`, `IngestionHub.route_packet`, and `DataFlowRouter.handle_data_flow`, while supporting list and CSV coordinate strings in `ElementResolver`.
- **Multi-Segment Jam Unpacking & Combined Edge Kinetics**: `GraphManager._ingest_global_jams_feed` projects each polyline in global `jams` arrays (`line: [{x, y}, ...]`) into local metric coordinates via `GeoProjectionService` and matches it to its exact `MapEdge` via `FastMapMatcher`, while `EdgeHydrodynamicsEngine` simultaneously extracts macroscopic volume (`flow` / `count`) and direct speed (`measured_speed_ms`).
- **`HISTORICAL` Warmup Incident Isolation**: During initial warmup (`active_mode == "HISTORICAL"`), `EdgePayloadFormatter` isolates global incident lists (`detection_list`), preventing false congestion spikes before live telemetry (`ONLINE` / `HYBRID`) activates.

---

## 2. HFT-Link Protocol Buffers Specification

Telemetry and neural snapshots are serialized using Protocol Buffers v3 (`proto/synapse_hft.proto`) to achieve sub-millisecond serialization:

```protobuf
syntax = "proto3";

package synapse.hft;

service HFTLink {
  rpc Ping (Empty) returns (SystemState);
  rpc LoadScenario (ScenarioDefinition) returns (ScenarioStatus);
  rpc SystemControl (ControlCommand) returns (CommandResponse);
  rpc StreamTraffic (stream TrafficFrame) returns (SystemState);
}

message TrafficFrame {
  double timestamp = 1;
  uint64 sequence_id = 2;
  map<string, EdgeState> edges = 3;
}

message EdgeState {
  float occupancy = 1;
  float mean_speed = 2;
  int32 queue_length = 3;
  float density = 4;
}
```

---

## 3. High-Frequency Streaming to CARINA

The `HftStreamer` (`src/hft/hft_streamer.py`, `src/hft/grpc_connector.py`) establishes an HTTP/2 persistent gRPC channel directly into downstream traffic light controllers like **CARINA CORE**:

- **Latency Guarantee**: End-to-end pipeline latency (sensor ingestion $\rightarrow$ neural inference $\rightarrow$ gRPC delivery) operates strictly below **250 ms**.
- **Zero-Copy Serialization**: Tensors are flattened directly into Protobuf byte buffers to avoid memory allocation bottlenecks.
- **Backpressure Regulation**: Dynamic sliding window buffering ensures slow consumers do not block real-time inference loops.

---

## 4. Self-Healing Resilience & Circuit Breaker

The auto-recovery engine (`src/hft/hft_recovery.py`) guards against network interruptions:

1. **Exponential Backoff with Full Jitter**:
   $$T_{\text{wait}} = \min(T_{\max}, T_{\text{base}} \cdot 2^{\text{attempt}}) \cdot \mathcal{U}(0.5, 1.5)$$
2. **Circuit Breaker Pattern**: If consecutive transmission attempts fail, the circuit trips to `OPEN`, immediately diverting data to local ring buffers and alerting the `FenixProcessSupervisor`.
3. **Seamless Resynchronization**: Once connectivity is restored, the circuit transitions to `HALF-OPEN`, flushing accumulated critical telemetry before resuming live streaming.

---

## 5. High-Throughput Go Gateway & Reverse Tunnel

1. **Go Gateway Daemon (`src_go`)**: Standalone binary (`bin/synapse-gateway`) processing raw network sockets and communicating via zero-port anonymous pipes (`STDIN`/`STDOUT`) with `src/go/subprocess_transport.py`.
2. **Dynamic DNS (DuckDNS)**: Embedded updater (`src_go/internal/tunnel/duckdns.go`) refreshing global IPv4/IPv6 addresses every 10 minutes, coordinated with `src/handlers/duckdns_handler.py`.
3. **Automated HTTPS Reverse Proxy (Caddy)**: Pre-compiled binary (`bin/caddy`) orchestrated by `src_go/internal/tunnel/caddy.go`, dynamically managing `config/Caddyfile` with automated Let's Encrypt / ZeroSSL TLS certificates.

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
