# 🗂️ SYNAPSE: Entités de Domaine et Schémas Spatiaux

Ce document décrit les entités de domaine, la modélisation du graphe spatial, la hiérarchie de confiance Bayésienne et la machine à états Zero-Trust définies dans `src/domain/entities.py`.

⬅️ [Hub de Documentation](README.md) | 🏛️ [Architecture Système](architecture.md) | 🧠 [Stack Neuronal MARKVART™](neural_models.md)

---

## 1. Entités de Topologie Spatiale

Le réseau routier urbain est représenté sous forme de multigraphe orienté $G = (V, E)$, implémenté par des dataclasses Python typées :

### `MapNode`
Représente une intersection, un point de décision ou un capteur virtuel :
- `node_id: str` : Identifiant unique (UUID ou identifiant OSM).
- `latitude: float`, `longitude: float` : Coordonnées géographiques WGS84.
- `elevation: float` : Altitude au-dessus du niveau de la mer (mètres).
- `node_type: NodeType` : Énumération (`INTERSECTION`, `RAMP`, `MIDBLOCK`, `BRIDGE`, `TUNNEL`).
- `connected_edges: List[str]` : Références vers les arêtes entrantes et sortantes.

### `MapEdge`
Représente un tronçon routier unidirectionnel connectant deux nœuds :
- `edge_id: str` : Identifiant unique du tronçon.
- `source_node_id: str`, `target_node_id: str` : Nœuds d'extrémité.
- `length_meters: float` : Longueur physique en mètres.
- `lanes: int` : Nombre de voies de circulation ($N_l \ge 1$).
- `speed_limit_kmh: float` : Vitesse maximale autorisée.
- `capacity_veh_per_hour: float` : Capacité maximale dérivée du modèle de Greenshields :
  $$C = v_f \cdot \frac{\rho_{\text{jam}}}{4}$$

---

## 2. Entités d'Ingestion et Sources de Données

### `DataSource`
Modélise une source de télémétrie physique ou virtuelle :
- `source_id: str` : Identifiant unique du fournisseur.
- `name: str` : Libellé descriptif.
- `source_type: SourceType` : Type de flux (`CAMERA`, `RADAR`, `INDUCTION_LOOP`, `BLUETOOTH`, `WAZE_API`, `TOMTOM_API`, `SUMO_SIM`).
- `protocol: IngestionProtocol` : Protocole de transport (`HTTP_POST`, `MQTT_TOPIC`, `WEBSOCKET`, `GRPC`).
- `trust_score: float` : Poids de confiance Bayésien dynamique ($0.0 \le \tau \le 1.0$).
- `status: SourceStatus` : État au sein de l'automate de validation.

---

## 3. Hiérarchie de Confiance Bayésienne

Afin d'empêcher les sources bruitées ou instables de fausser les tenseurs neuronaux, SYNAPSE fixe des probabilités a priori selon la proximité terrain du capteur :

$$\tau_{\text{initial}} = \begin{cases} 0.95 & \text{si Capteur Terrain Local (Boucles, Radars, Caméras de Bord)} \\ 0.60 & \text{si API Globale / Tiers (Waze, TomTom, Agrégateurs Mobiles)} \end{cases}$$

### Évolution Dynamique du Score
Le score est réévalué de manière continue en fonction de la vraisemblance physique des mesures :

$$\tau_{t+1} = \frac{\tau_t \cdot P(E \mid \text{Valide})}{\tau_t \cdot P(E \mid \text{Valide}) + (1 - \tau_t) \cdot P(E \mid \text{Anomalie})}$$

Si $\tau_t$ franchit à la baisse le seuil $\tau_{\text{seuil}} = 0.40$, la source est automatiquement dégradée.

---

## 4. Automate d'États Zero-Trust `SourceStatus`

```
              ┌───────────────┐
              │  QUARANTAINE  │ ◄── Réception initiale du flux
              └───────┬───────┘
                      │ Respect du schéma de données
              ┌───────▼───────┐
              │  EN VALIDATION│ ◄── Contrôle des bornes physiques ($|\Delta v| \le a_{\max}$)
              └───────┬───────┘
                      │ Paquets valides consécutifs ($N \ge 10$)
              ┌───────▼───────┐
       ┌────► │     ACTIF     │ ◄── Ingestion directe dans les tenseurs MARKVART
       │      └───────┬───────┘
Rétablissement│ Perte de paquets / timeout (> 3 cycles)
       │      ┌───────▼───────┐
       └───── │   FALLBACK    │ ◄── Extrapolation cinématique KSE
              └───────┬───────┘
                      │ Absence prolongée ou incohérence persistante
              ┌───────▼───────┐
              │    REJETÉ     │
              └───────────────┘
```

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
