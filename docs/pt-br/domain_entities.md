# 🗂️ SYNAPSE: Entidades de Domínio e Esquemas Espaciais

Este documento descreve as entidades de domínio fundamentais, a estrutura do grafo de topologia, a hierarquia de confiança Bayesiana e as máquinas de estado Zero-Trust definidas em `src/domain/entities.py`.

⬅️ [Central de Documentação](README.md) | 🏛️ [Arquitetura Central](architecture.md) | 🧠 [Stack Neural MARKVART™](neural_models.md)

---

## 1. Entidades da Topologia Espacial

A malha viária urbana é modelada como um multigrafo direcionado $G = (V, E)$, mapeado em dataclasses fortemente tipadas em Python (`src/domain/entities.py`):

### `MapNode`
Representa um cruzamento semaforizado ou junção viária na malha projetada SUMO em coordenadas métricas:
- `id: str`: Identificador único do nó/junção (ex: `"cluster_12048"`).
- `x: float`, `y: float`: Coordenadas cartesianas UTM 2D projetadas em metros.
- `node_type: str`: Tipologia da junção (`"traffic_light"`, `"priority"`, `"roundabout"`).
- `real_name: Optional[str]`: Nome legível da interseção viária urbana.
- `tl_logic_id: Optional[str]`: Identificador do plano semafórico (tlLogic) vinculando o nó ao controlador CARINA a jusante.

### `MapEdge`
Representa um segmento de via direcional conectando dois nós/interseções:
- `id: str`: Identificador único do trecho viário (ex: `"-edge_4401"`).
- `from_node: str`, `to_node: str`: Vértices delimitadores de origem e destino.
- `shape: List[Tuple[float, float]]`: Geometria detalhada da via (lista de pontos x, y em metros).
- `real_name: Optional[str]`: Nome legível do logradouro.
- `weight: float`: Custo de travessia para algoritmos de roteamento em grafo (padrão $1.0$).
- `length: float`: Extensão física do segmento em metros.
- `max_speed: float`: Velocidade máxima regulamentada em m/s (padrão $13.89\text{ m/s} \approx 50\text{ km/h}$).
- `lanes: int`: Quantidade de faixas de rolamento ativas ($N_l \ge 1$).
- `edge_type: str`: Classificação hierárquica viária OSM/SUMO (`"highway.primary"`, `"highway.secondary"`, `"highway.tertiary"`, `"highway.residential"`, `"highway.living_street"`, `"highway.unclassified"`).
- `priority: int`: Nível de prioridade física na malha viária (`-1` quando não especificado).
- `signal_group_id: int`: Grupo focal NTCIP que comanda o descarregamento na junção (`-1` se livre).
- **Papel Físico e Neural**: Seus atributos compõem o tensor físico 5D de arestas (`edge_attr` $\in \mathbb{R}^{E \times 5}$) utilizado pelo `DiffusionGATv2` e governam os pesos de permeabilidade hidrodinâmica no `TrafficHydrodynamicEngine`.

---

## 2. Entidades de Ingestão e Fontes de Dados

### `DataSource`
Entidade central de telemetria representando uma fonte interna ou externa (Esquema Flexível V5):
- `id: str`: Identificador único da fonte (ex: `"src_1"`).
- `name: str`: Rótulo legível do sensor.
- `source_type: SourceType`: Enumeração (`CSV`, `PARQUET`, `API`, `MQTT`, `DATABASE`, `SUMO_NET_XML`).
- `connection_string: str`: URI do endpoint, tópico de broker ou caminho de arquivo.
- `is_local: bool`: Distingue sensores físicos locais de feeds de nuvem globais.
- `status: SourceStatus`: Estado no ciclo de validação (`QUARANTINE`, `VALIDATING`, `ACTIVE`, `FALLBACK`, `PROBATION`, `REJECTED`, `OFFLINE`).
- `lat: float`, `lon: float`: Coordenadas geográficas WGS84 para projeção espacial.
- `latest_value: Any`: Campo polimórfico que suporta valores escalares, listas ou dicionários de detecção CV.
- `last_update: float`: Timestamp Unix do último pacote recebido.
- `semantic_type: Optional[str]`: Categoria semântica inferida (`"speed"`, `"flow"`, `"occupancy"`).
- `inferred_unit: Optional[str]`: Unidade de engenharia detectada (`"km/h"`, `"m/s"`, `"veh/h"`).
- `confidence_score: float`: Grau de confiança Bayesiana dinâmico ($0.0 \le \tau \le 1.0$).
- `metadata: Dict[str, Any]`: Dicionário extensível para configurações específicas do sensor (IPs, calibração, sensibilidade de laço).

### `DataAssociation`
Representa o vínculo lógico entre uma `DataSource` e um `MapNode` ou `MapEdge`:
- `source_id: str`: Referência ao identificador da fonte (`DataSource.id`).
- `element_id: str`: Identificador do elemento de destino (`MapNode.id` ou `MapEdge.id`).
- `channel: Optional[str]`: Subcanal ou faixa de rolamento específica para sensores bidirecionais ou multicanais.

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
