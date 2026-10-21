# ⚡ SYNAPSE: Ingestion de Données et Transport gRPC HFT-Link

Ce document décrit le concentrateur d'ingestion multiprotocole, la spécification Protocol Buffers v3 et l'architecture de transmission gRPC à très basse latence avec résilience autonome.

⬅️ [Hub de Documentation](README.md) | ⏱️ [Phases d'Exécution](execution_phases.md) | 🖥️ [Interface Desktop](ui_architecture.md)

---

## 1. Concentrateur d'Ingestion Multiprotocole

L'Ingestion Hub (`src/infrastructure/ingestion/`) met à disposition des adaptateurs pour normaliser les données hétérogènes :

- **Ingestion HTTP** : Points d'accès REST pour l'ingestion de données de trafic externes (Waze CCP, TomTom Move).
- **Client Broker MQTT** : Souscription aux thématiques de télémétrie des unités de bord de route (RSU) et des boucles (`traffic/sensors/#`).
- **Passerelle WebSocket** : Flux continus bidirectionnels à faible latence pour radars routiers.
- **Passerelle Haute Performance en Go** : Binaire compilé autonome (`synapse-go`) recevant les trames réseau à haut débit sans surcharge de l'interpréteur Python.

---

## 2. Schéma Protocol Buffers v3 (HFT-Link)

La sérialisation haute performance s'appuie sur Protocol Buffers v3 (`proto/synapse_hft.proto`) :

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

## 3. Streaming Haute Fréquence vers CARINA

Le composant `HftStreamer` maintient une session gRPC permanente sur HTTP/2 pour délivrer l'état du réseau aux contrôleurs de feux **CARINA CORE** :

- **Garantie de Latence** : La latence de bout en bout (ingestion capteur $\rightarrow$ inférence neuronale $\rightarrow$ transmission gRPC) est rigoureusement maintenue en dessous de **250 ms**.
- **Sérialisation Zero-Copy** : Les tenseurs PyTorch sont directement linéarisés dans les tampons d'octets Protobuf.
- **Contrôle de Contre-Pression** : Des fenêtres glissantes dynamiques protègent la boucle d'inférence contre les ralentissements de clients distants.

---

## 4. Résilience Autonome et Disjoncteur (Circuit Breaker)

Le mécanisme de reprise (`src/infrastructure/hft_recovery.py`) gère les ruptures de communication réseau :

1. **Backoff Exponentiel avec Jitter Aléatoire** :
   $$T_{\text{attente}} = \min(T_{\max}, T_{\text{base}} \cdot 2^{\text{tentative}}) \cdot \mathcal{U}(0.5, 1.5)$$
2. **Patron Circuit Breaker** : Si 5 tentatives successives échouent, le disjoncteur bascule à `OPEN`, conservant les trames dans des mémoires tampons circulaires et alertant F.E.N.I.X.
3. **Resynchronisation Progressive** : Lors du rétablissement du réseau, le circuit passe à `HALF-OPEN` et purge les données accumulées avant de stabiliser le flux en direct.

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
