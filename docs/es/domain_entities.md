# 🗂️ SYNAPSE: Entidades de Dominio y Esquemas Espaciales

Este documento describe las entidades de dominio fundamentales, la estructura del grafo topológico, la jerarquía de confianza Bayesiana y la máquina de estados Zero-Trust definidas en `src/domain/entities.py`.

⬅️ [Centro de Documentación](README.md) | 🏛️ [Arquitectura Central](architecture.md) | 🧠 [Stack Neural MARKVART™](neural_models.md)

---

## 1. Entidades de Topología Espacial

La red vial urbana se modela como un multigrafo dirigido $G = (V, E)$, expresado mediante dataclasses fuertemente tipadas en Python:

### `MapNode`
Representa una intersección semaforizada, un punto de bifurcación o un sensor virtual:
- `node_id: str`: Identificador único (UUID o código OSM municipal).
- `latitude: float`, `longitude: float`: Coordenadas geográficas WGS84.
- `elevation: float`: Altitud sobre el nivel del mar en metros.
- `node_type: NodeType`: Enumeración (`INTERSECTION`, `RAMP`, `MIDBLOCK`, `BRIDGE`, `TUNNEL`).
- `connected_edges: List[str]`: Referencias a segmentos viales entrantes y salientes.

### `MapEdge`
Representa un segmento vial unidireccional que conecta dos nodos:
- `edge_id: str`: Identificador único del segmento.
- `source_node_id: str`, `target_node_id: str`: Nodos límite del segmento.
- `length_meters: float`: Longitud física en metros.
- `lanes: int`: Número de carriles activos ($N_l \ge 1$).
- `speed_limit_kmh: float`: Límite reglamentario de velocidad.
- `capacity_veh_per_hour: float`: Capacidad vial máxima derivada del modelo de Greenshields:
  $$C = v_f \cdot \frac{\rho_{\text{jam}}}{4}$$

---

## 2. Entidades de Ingestión y Fuentes de Datos

### `DataSource`
Modela una fuente de telemetría física o virtual:
- `source_id: str`: Identificador único del proveedor.
- `name: str`: Etiqueta descriptiva para operadores humanos.
- `source_type: SourceType`: (`CAMERA`, `RADAR`, `INDUCTION_LOOP`, `BLUETOOTH`, `WAZE_API`, `TOMTOM_API`, `SUMO_SIM`).
- `protocol: IngestionProtocol`: Protocolo de transporte (`HTTP_POST`, `MQTT_TOPIC`, `WEBSOCKET`, `GRPC`).
- `trust_score: float`: Peso Bayesiano dinámico de confiabilidad ($0.0 \le \tau \le 1.0$).
- `status: SourceStatus`: Estado en la máquina de validación Zero-Trust.

---

## 3. Jerarquía de Confianza Bayesiana

Para evitar que datos corruptos o APIs externas con latencia degraden las matrices neuronales, SYNAPSE establece pesos a priori según la cercanía física del sensor al terreno:

$$\tau_{\text{inicial}} = \begin{cases} 0.95 & \text{si Sensor Local en Terreno (Espiras, Radares, Cámaras de Borde)} \\ 0.60 & \text{si API Global / Terceros (Waze, TomTom, Agregadores Celulares)} \end{cases}$$

### Actualización Bayesiana Dinámica
La confiabilidad evoluciona de manera recursiva según la consistencia física observada:

$$\tau_{t+1} = \frac{\tau_t \cdot P(E \mid \text{Válido})}{\tau_t \cdot P(E \mid \text{Válido}) + (1 - \tau_t) \cdot P(E \mid \text{Fallo})}$$

Si $\tau_t$ cae por debajo de $\tau_{\text{umbral}} = 0.40$, la fuente se degrada de manera automática.

---

## 4. Máquina de Estados Zero-Trust `SourceStatus`

```
              ┌───────────────┐
              │  CUARENTENA   │ ◄── Recepción inicial de datos
              └───────┬───────┘
                      │ Cumple esquema de datos
              ┌───────▼───────┐
              │   VALIDANDO   │ ◄── Comprobación de límites físicos ($|\Delta v| \le a_{\max}$)
              └───────┬───────┘
                      │ Paquetes válidos consecutivos ($N \ge 10$)
              ┌───────▼───────┐
       ┌────► │    ACTIVO     │ ◄── Ingestión directa en tensores MARKVART
       │      └───────┬───────┘
Recuperación  │ Pérdida de paquetes / timeout (> 3 ciclos sin datos)
       │      ┌───────▼───────┐
       └───── │   FALLBACK    │ ◄── Estimación cinemática KSE Dead Reckoning
              └───────┬───────┘
                      │ Ausencia prolongada o datos corruptos
              ┌───────▼───────┐
              │   RECHAZADO   │
              └───────────────┘
```

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
