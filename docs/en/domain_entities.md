# 🗂️ SYNAPSE: Domain Entities & Spatial Schemas

This document details the core domain entities, topology graph structures, Bayesian trust score hierarchy, and Zero-Trust validation state machines defined in `src/domain/entities.py`.

⬅️ [Documentation Hub](README.md) | 🏛️ [Core Architecture](architecture.md) | 🧠 [MARKVART™ Neural Stack](neural_models.md)

---

## 1. Spatial Topology Entities

The urban traffic graph is represented as a directed multigraph $G = (V, E)$, mapped to strongly-typed Python dataclasses (`src/domain/entities.py`):

### `MapNode`
Represents an urban traffic intersection or junction in the projected metric SUMO network:
- `id: str`: Unique junction identifier (e.g., `"cluster_12048"`).
- `x: float`, `y: float`: Projected 2D UTM cartesian coordinates in meters.
- `node_type: str`: Junction typology (`"traffic_light"`, `"priority"`, `"roundabout"`).
- `real_name: Optional[str]`: Human-readable street name intersection.
- `tl_logic_id: Optional[str]`: Controlling Traffic Light Logic ID linking the node to downstream CARINA controllers.

### `MapEdge`
Represents a directional roadway segment connecting two intersections:
- `id: str`: Unique edge identifier (e.g., `"-edge_4401"`).
- `from_node: str`, `to_node: str`: Boundary source and target junction node IDs.
- `shape: List[Tuple[float, float]]`: Detailed polyline geometry coordinates in meters.
- `real_name: Optional[str]`: Human-readable street name.
- `weight: float`: Edge traversal cost for routing algorithms (default $1.0$).
- `length: float`: Physical segment length in meters.
- `max_speed: float`: Speed limit in m/s (default $13.89\text{ m/s} \approx 50\text{ km/h}$).
- `lanes: int`: Number of parallel vehicular lanes ($N_l \ge 1$).
- `edge_type: str`: OSM/SUMO road hierarchy classification (`"highway.primary"`, `"highway.secondary"`, `"highway.tertiary"`, `"highway.residential"`, `"highway.living_street"`, `"highway.unclassified"`).
- `priority: int`: Physical road priority rank (`-1` default when unspecified).
- `signal_group_id: int`: NTCIP signal group phase controlling vehicular discharge into the junction (`-1` if uncontrolled).
- **Physical & Neural Role**: Supplies the 5D physical edge tensor (`edge_attr` $\in \mathbb{R}^{E \times 5}$) consumed by `DiffusionGATv2` and governs road-hierarchy hydrodynamic permeability in `TrafficHydrodynamicEngine`.

---

## 2. Ingestion & Data Source Entities

### `DataSource`
The core ingestion entity representing an internal or external telemetry provider (V5 Flexible Schema):
- `id: str`: Unique internal source identifier (e.g., `"src_1"`).
- `name: str`: Descriptive human-readable sensor label.
- `source_type: SourceType`: Enum (`CSV`, `PARQUET`, `API`, `MQTT`, `DATABASE`, `SUMO_NET_XML`).
- `connection_string: str`: Endpoint URI, broker connection string, or file path.
- `is_local: bool`: Distinguishes ground-truth local sensors from global feeds.
- `status: SourceStatus`: Current state in the zero-trust lifecycle (`QUARANTINE`, `VALIDATING`, `ACTIVE`, `FALLBACK`, `PROBATION`, `REJECTED`, `OFFLINE`).
- `lat: float`, `lon: float`: WGS84 coordinates for spatial projection.
- `latest_value: Any`: Flexible payload holder supporting scalar floats, lists, or CV detection dictionaries.
- `last_update: float`: Unix timestamp of the most recent telemetry tick.
- `semantic_type: Optional[str]`: Classified semantic category (`"speed"`, `"flow"`, `"occupancy"`).
- `inferred_unit: Optional[str]`: Classified engineering unit (`"km/h"`, `"m/s"`, `"veh/h"`).
- `confidence_score: float`: Dynamic Bayesian reliability weight ($0.0 \le \tau \le 1.0$).
- `metadata: Dict[str, Any]`: Extensible dictionary for device-specific attributes (IPs, camera calibration, loop sensitivity).

### `DataAssociation`
Represents the logical link connecting a `DataSource` to a `MapNode` or `MapEdge`:
- `source_id: str`: Reference to the `DataSource.id`.
- `element_id: str`: Target `MapNode.id` or `MapEdge.id`.
- `channel: Optional[str]`: Sub-channel or specific lane identifier for multi-lane / bidirectional sensor hardware.

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
