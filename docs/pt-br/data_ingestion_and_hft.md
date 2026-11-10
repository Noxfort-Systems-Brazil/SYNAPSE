# ⚡ SYNAPSE: Ingestão de Dados e Transporte gRPC HFT-Link

Este documento descreve a arquitetura do hub de ingestão sensorial multiprotocolo, as especificações de Protocol Buffers v3 e o pipeline gRPC de alta frequência com resiliência autônoma.

⬅️ [Central de Documentação](README.md) | ⏱️ [Fases de Execução](execution_phases.md) | 🖥️ [Interface Desktop](ui_architecture.md)

---

## 1. Hub de Ingestão Multiprotocolo

O Ingestion Hub (`src/adapters/ingestion_hub.py` e `src/engine/ingestion_pipeline.py`) gerencia adaptadores para múltiplos protocolos industriais e web:

- **Ingestão HTTP**: Endpoints REST para recepção de dados agregados de tráfego de terceiros (Waze CCP, TomTom Move).
- **Cliente Broker MQTT**: Inscrição em tópicos de estações de beira de pista (RSUs) e controladores de laço (`traffic/sensors/#`).
- **Gateway WebSocket**: Conexões persistentes bidirecionais de baixa latência para radares em tempo real.
- **Gateway de Alta Performance em Go**: Binário compilado nativo (`synapse-go`) processando sockets brutos sem sobrecarga do interpretador Python.
- **Resolução Canônica de Alias (`device_id_map`)**: Traduz automaticamente apelidos de hardware enviados no payload (ex: `loop_01`) para o identificador canônico da fonte registrada (ex: `src_2`) no `IngestionPipeline`, `IngestionHub.route_packet` e `DataFlowRouter.handle_data_flow`, além de suportar coordenadas em formato lista ou string CSV no `ElementResolver`.
- **Desempacotamento Multi-Segmento de Jams e Cinética Combinada**: O `GraphManager._ingest_global_jams_feed` projeta cada polilinha da lista `jams` (`line: [{x, y}, ...]`) para metros locais via `GeoProjectionService` e faz o map-matching individual via `FastMapMatcher`, enquanto o `EdgeHydrodynamicsEngine` extrai simultaneamente fluxo/contagem e velocidade direta (`measured_speed_ms`).
- **Isolamento de Incidentes no Warmup (`HISTORICAL`)**: Durante o aquecimento inicial (`active_mode == "HISTORICAL"`), o `EdgePayloadFormatter` isola listas globais de incidentes (`detection_list`), evitando falsos alertas de congestionamento antes da ativação de telemetria em tempo real (`ONLINE` / `HYBRID`).

---

## 2. Esquema Protocol Buffers v3 (HFT-Link)

A comunicação de alta frequência utiliza Protocol Buffers v3 (`proto/synapse_hft.proto`):

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

## 3. Streaming de Alta Frequência para o CARINA

O módulo `HftStreamer` (`src/hft/hft_streamer.py`, `src/hft/grpc_connector.py`) gerencia conexões HTTP/2 gRPC contínuas para alimentar os controladores semafóricos **CARINA CORE**:

- **Garantia de Latência**: O atraso ponta a ponta (ingestão sensorial $\rightarrow$ inferência neural $\rightarrow$ entrega gRPC) permanece rigorosamente inferior a **250 ms**.
- **Serialização de Cópia Zero**: Tensores PyTorch são achatados diretamente em buffers Protobuf, minimizando alocações de memória.
- **Controle de Contrapressão**: Janelas de transmissão dinâmicas impedem que clientes lentos travem a inferência de tempo real.

---

## 4. Resiliência Autônoma e Circuit Breaker

O mecanismo de recuperação (`src/hft/hft_recovery.py`) protege contra indisponibilidades de rede:

1. **Backoff Exponencial com Jitter Completo**:
   $$T_{\text{espera}} = \min(T_{\max}, T_{\text{base}} \cdot 2^{\text{tentativa}}) \cdot \mathcal{U}(0.5, 1.5)$$
2. **Padrão Circuit Breaker**: Se tentativas consecutivas falharem, o circuito abre (`OPEN`), retendo dados em buffers circulares de contingência e notificando o `FenixProcessSupervisor`.
3. **Ressincronização Automática**: Ao restabelecer a conectividade, o circuito entra em `HALF-OPEN`, transmitindo a telemetria acumulada antes de normalizar o fluxo.

---

## 5. Gateway de Alta Performance em Go & Túnel Reverso Seguro

1. **Daemon do Go Gateway (`src_go`)**: Binário compilado (`bin/synapse-gateway`) para processamento de sockets em alta taxa com transmissão zero-port via pipes anônimos (`STDIN`/`STDOUT`) para `src/go/subprocess_transport.py`.
2. **DNS Dinâmico (DuckDNS)**: Driver nativo em Go (`src_go/internal/tunnel/duckdns.go`) atualizando endereços globais IPv4/IPv6 a cada 10 minutos em coordenação com `src/handlers/duckdns_handler.py`.
3. **Proxy Reverso HTTPS Automatizado (Caddy)**: Binário (`bin/caddy`) coordenado por `src_go/internal/tunnel/caddy.go`, gerenciando dinamicamente o `config/Caddyfile` com emissão automática de certificados TLS (Let's Encrypt / ZeroSSL) para conexões externas seguras.

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
