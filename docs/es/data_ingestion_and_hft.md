# ⚡ SYNAPSE: Ingestión de Datos y Transporte gRPC HFT-Link

Este documento especifica el concentrador de ingestión multiprotocolo, el esquema de Protocol Buffers v3 y la arquitectura de transmisión gRPC de alta frecuencia con autorecuperación.

⬅️ [Centro de Documentación](README.md) | ⏱️ [Fases de Ejecución](execution_phases.md) | 🖥️ [Interfaz de Escritorio](ui_architecture.md)

---

## 1. Concentrador de Ingestión Multiprotocolo

El Ingestion Hub (`src/infrastructure/ingestion/`) proporciona conectores estandarizados para diversos protocolos:

- **Ingestión HTTP**: Puntos de enlace REST para fuentes agregadas de tráfico (Waze CCP, TomTom Move).
- **Cliente Broker MQTT**: Suscripción a tópicos de telemetría de unidades de borde (RSUs) y espiras inductivas (`traffic/sensors/#`).
- **Pasarela WebSocket**: Canales persistentes de baja latencia para radares vehiculares.
- **Pasarela de Alto Rendimiento en Go**: Binario compilado nativo (`synapse-go`) para procesar sockets de red crudos a velocidad de línea.

---

## 2. Especificación Protocol Buffers v3 (HFT-Link)

La transmisión de alta frecuencia emplea Protocol Buffers v3 (`proto/synapse_hft.proto`):

```protobuf
syntax = "proto3";

package synapse.hft;

service HftLinkService {
  rpc StreamSnapshots(SnapshotRequest) returns (stream TrafficSnapshot);
  rpc SendTelemetryBatch(TelemetryBatch) returns (IngestionResponse);
}

message TrafficSnapshot {
  int64 timestamp_ns = 1;
  string snapshot_id = 2;
  repeated EdgeMetrics edges = 3;
  repeated NodeMetrics nodes = 4;
  repeated float density_matrix = 5;
  int32 confidence_score = 6;
}

message EdgeMetrics {
  string edge_id = 1;
  float density_veh_km = 2;
  float mean_speed_kmh = 3;
  float occupancy_ratio = 4;
  int32 source_status = 5;
}
```

---

## 3. Streaming de Alta Frecuencia hacia CARINA

El componente `HftStreamer` sostiene canales gRPC continuos sobre HTTP/2 para suministrar datos en tiempo real al controlador semafórico **CARINA CORE**:

- **Garantía de Latencia**: Latencia integral de procesamiento y transmisión garantizada por debajo de **250 ms**.
- **Serialización Cero-Copia**: Aplanamiento directo de tensores a buffers de bytes Protobuf.
- **Control de Contrapresión**: Ventanas dinámicas de transmisión que evitan bloqueos por receptores lentos.

---

## 4. Resiliencia Automática y Circuit Breaker

El módulo `src/infrastructure/hft_recovery.py` gestiona contingencias de conectividad:

1. **Backoff Exponencial con Jitter**:
   $$T_{\text{espera}} = \min(T_{\max}, T_{\text{base}} \cdot 2^{\text{intento}}) \cdot \mathcal{U}(0.5, 1.5)$$
2. **Patrón Circuit Breaker**: Tras 5 fallos consecutivos, el circuito conmuta a `OPEN`, reteniendo datos en buffers circulares y notificando al supervisor F.E.N.I.X.
3. **Resincronización Suave**: Al restablecerse la red, conmuta a `HALF-OPEN`, drenando la telemetría acumulada antes de reanudar el flujo en vivo.

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
