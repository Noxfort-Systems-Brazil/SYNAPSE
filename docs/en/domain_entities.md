# 🗂️ SYNAPSE: Domain Entities & Spatial Schemas

This document details the core domain entities, topology graph structures, Bayesian trust score hierarchy, and Zero-Trust validation state machines defined in `src/domain/entities.py`.

⬅️ [Documentation Hub](README.md) | 🏛️ [Core Architecture](architecture.md) | 🧠 [MARKVART™ Neural Stack](neural_models.md)

---

## 1. Spatial Topology Entities

The urban traffic graph is represented as a directed multigraph $G = (V, E)$, mapped to strongly-typed Python dataclasses:

### `MapNode`
Represents an intersection, roadway decision point, or virtual sensing coordinate:
- `node_id: str`: Unique UUID or municipal OSM identifier.
- `latitude: float`, `longitude: float`: WGS84 geographic coordinates.
- `elevation: float`: Altitude above sea level in meters.
- `node_type: NodeType`: Enum (`INTERSECTION`, `RAMP`, `MIDBLOCK`, `BRIDGE`, `TUNNEL`).
- `connected_edges: List[str]`: Outgoing and incoming edge references.

### `MapEdge`
Represents a directional roadway segment connecting two nodes:
- `edge_id: str`: Unique UUID string.
- `source_node_id: str`, `target_node_id: str`: Directional boundary vertices.
- `length_meters: float`: Physical segment length.
- `lanes: int`: Number of active traffic lanes ($N_l \ge 1$).
- `speed_limit_kmh: float`: Legal maximum speed limit.
- `edge_type: str`: OSM/SUMO road hierarchy classification extracted from `.net.xml.gz` (`"highway.primary"`, `"highway.secondary"`, `"highway.tertiary"`, `"highway.residential"`, `"highway.living_street"`, `"highway.unclassified"`).
- `priority: int`: SUMO physical road priority rank (`-1` default).
- `capacity_veh_per_hour: float`: Maximum roadway capacity derived from the Greenshields model:
  $$C = v_f \cdot \frac{\rho_{\text{jam}}}{4}$$
- **Physical & Neural Role**: Supplies the 5D physical edge tensor (`edge_attr` $\in \mathbb{R}^{E \times 5}$) consumed by `DiffusionGATv2` and governs road-hierarchy hydrodynamic permeability in `TrafficHydrodynamicEngine`.

---

## 2. Ingestion & Data Source Entities

### `DataSource`
Encapsulates physical or virtual telemetry feeds:
- `source_id: str`: Unique provider identifier.
- `name: str`: Descriptive human-readable label.
- `source_type: SourceType`: Enum (`CAMERA`, `RADAR`, `INDUCTION_LOOP`, `BLUETOOTH`, `WAZE_API`, `TOMTOM_API`, `SUMO_SIM`).
- `protocol: IngestionProtocol`: (`HTTP_POST`, `MQTT_TOPIC`, `WEBSOCKET`, `GRPC`).
- `trust_score: float`: Dynamic Bayesian reliability weight ($0.0 \le \tau \le 1.0$).
- `status: SourceStatus`: Current state in the zero-trust validation machine.

---

## 3. Bayesian Trust Score Hierarchy

To prevent spoofed, noisy, or failing third-party APIs from corrupting neural tensors, SYNAPSE assigns initial Bayesian trust priors based on sensor proximity:

$$\tau_{\text{initial}} = \begin{cases} 0.95 & \text{if Local Ground-Truth (Loops, Dedicated Radars, Edge Vision)} \\ 0.60 & \text{if Global / Third-Party (Cloud Crowdsourced APIs, Cellular Aggregators)} \end{cases}$$

### Dynamic Trust Score Evolution
Trust scores are continuously updated following evidence of physical consistency:

$$\tau_{t+1} = \frac{\tau_t \cdot P(E \mid \text{Valid})}{\tau_t \cdot P(E \mid \text{Valid}) + (1 - \tau_t) \cdot P(E \mid \text{Fault})}$$

If $\tau_t$ drops below $\tau_{\text{threshold}} = 0.40$, the data source is automatically downgraded.

---

## 4. `SourceStatus` Zero-Trust State Machine

```
              ┌───────────────┐
              │  QUARANTINE   │ ◄── Initial Intake
              └───────┬───────┘
                      │ Pass format & semantic schema
              ┌───────▼───────┐
              │  VALIDATING   │ ◄── Physical Bounds Checking ($|\Delta v| \le a_{\max}$)
              └───────┬───────┘
                      │ Consecutive valid packets ($N \ge 10$)
              ┌───────▼───────┐
       ┌────► │    ACTIVE     │ ◄── Ingested directly into MARKVART Tensors
       │      └───────┬───────┘
Recovery (Heartbeat)  │ Packet loss / timeout (> 3 missed cycles)
       │      ┌───────▼───────┐
       └───── │   FALLBACK    │ ◄── KSE Kinematic Dead Reckoning
              └───────┬───────┘
                      │ Extended timeout or invalid data pattern
              ┌───────▼───────┐
              │   REJECTED    │
              └───────────────┘
```

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
