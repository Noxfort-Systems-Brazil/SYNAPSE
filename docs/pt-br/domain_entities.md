# 🗂️ SYNAPSE: Entidades de Domínio e Esquemas Espaciais

Este documento descreve as entidades de domínio fundamentais, a estrutura do grafo de topologia, a hierarquia de confiança Bayesiana e as máquinas de estado Zero-Trust definidas em `src/domain/entities.py`.

⬅️ [Central de Documentação](README.md) | 🏛️ [Arquitetura Central](architecture.md) | 🧠 [Stack Neural MARKVART™](neural_models.md)

---

## 1. Entidades da Topologia Espacial

A malha viária urbana é modelada como um multigrafo direcionado $G = (V, E)$, mapeado em dataclasses tipadas em Python:

### `MapNode`
Representa um cruzamento semaforizado, nó de decisão viária ou sensor virtual:
- `node_id: str`: Identificador único (UUID ou código OSM municipal).
- `latitude: float`, `longitude: float`: Coordenadas geográficas WGS84.
- `elevation: float`: Altitude em relação ao nível do mar (metros).
- `node_type: NodeType`: Enumeração (`INTERSECTION`, `RAMP`, `MIDBLOCK`, `BRIDGE`, `TUNNEL`).
- `connected_edges: List[str]`: Lista de identificadores de arestas conectadas.

### `MapEdge`
Representa um segmento de via direcional conectando dois nós:
- `edge_id: str`: Identificador único do trecho.
- `source_node_id: str`, `target_node_id: str`: Vértices delimitadores da via.
- `length_meters: float`: Extensão física do segmento em metros.
- `lanes: int`: Quantidade de faixas de rolamento ativas ($N_l \ge 1$).
- `speed_limit_kmh: float`: Velocidade regulamentada máxima.
- `edge_type: str`: Classificação hierárquica OSM/SUMO extraída do `.net.xml.gz` (`"highway.primary"`, `"highway.secondary"`, `"highway.tertiary"`, `"highway.residential"`, `"highway.living_street"`, `"highway.unclassified"`).
- `priority: int`: Prioridade viária física na topologia SUMO (`-1` por padrão).
- `capacity_veh_per_hour: float`: Capacidade máxima da via derivada da equação de Greenshields:
  $$C = v_f \cdot \frac{\rho_{\text{jam}}}{4}$$
- **Papel Físico e Neural**: Seus atributos compõem o tensor físico 5D de arestas (`edge_attr` $\in \mathbb{R}^{E \times 5}$) utilizado pelo `DiffusionGATv2` e governam os pesos de permeabilidade hidrodinâmica no `TrafficHydrodynamicEngine`.

---

## 2. Entidades de Ingestão e Fontes de Dados

### `DataSource`
Encapsula uma fonte transmissora de telemetria (física ou virtual):
- `source_id: str`: Identificador único do provedor.
- `name: str`: Rótulo descritivo do sensor.
- `source_type: SourceType`: Enumeração (`CAMERA`, `RADAR`, `INDUCTION_LOOP`, `BLUETOOTH`, `WAZE_API`, `TOMTOM_API`, `SUMO_SIM`).
- `protocol: IngestionProtocol`: Protocolo de transporte (`HTTP_POST`, `MQTT_TOPIC`, `WEBSOCKET`, `GRPC`).
- `trust_score: float`: Peso Bayesiano dinâmico de confiabilidade ($0.0 \le \tau \le 1.0$).
- `status: SourceStatus`: Estado corrente na máquina de validação Zero-Trust.

---

## 3. Hierarquia de Confiança Bayesiana

Para impedir que dados ruidosos, forjados ou APIs externas instáveis degradem os tensores da rede neural, o SYNAPSE atribui pesos Bayesianos a priori baseados na proximidade do sensor com o solo:

$$\tau_{\text{inicial}} = \begin{cases} 0.95 & \text{se Sensor Local Terrestre (Laços Indutivos, Radares, Visão Local)} \\ 0.60 & \text{se API Global / Terceiros (Crowdsourcing Waze/TomTom, Agregadores Celulares)} \end{cases}$$

### Atualização Dinâmica da Confiabilidade
O índice de confiança é atualizado dinamicamente com base na plausibilidade física dos pacotes:

$$\tau_{t+1} = \frac{\tau_t \cdot P(E \mid \text{Válido})}{\tau_t \cdot P(E \mid \text{Válido}) + (1 - \tau_t) \cdot P(E \mid \text{Falha})}$$

Se $\tau_t$ cair abaixo de $\tau_{\text{limite}} = 0,40$, a fonte é automaticamente rebaixada.

---

## 4. Máquina de Estados Zero-Trust `SourceStatus`

```
              ┌───────────────┐
              │  QUARENTENA   │ ◄── Recepção inicial de dados
              └───────┬───────┘
                      │ Conformidade com esquema e limites
              ┌───────▼───────┐
              │   VALIDANDO   │ ◄── Verificação de aceleração física ($|\Delta v| \le a_{\max}$)
              └───────┬───────┘
                      │ Pacotes válidos consecutivos ($N \ge 10$)
              ┌───────▼───────┐
       ┌────► │     ATIVO     │ ◄── Ingestão direta nos tensores MARKVART
       │      └───────┬───────┘
Recuperação   │ Perda de pacotes / timeout (> 3 ciclos sem dados)
       │      ┌───────▼───────┐
       └───── │   FALLBACK    │ ◄── Estimativa cinemática KSE Dead Reckoning
              └───────┬───────┘
                      │ Inconsistência grave ou ausência prolongada
              ┌───────▼───────┐
              │   REJEITADO   │
              └───────────────┘
```

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
