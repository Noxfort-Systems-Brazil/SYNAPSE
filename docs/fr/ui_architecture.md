# 🖥️ SYNAPSE: Architecture UI et IPC Stdio Zero-Port

Ce document spécifie l'architecture logicielle de l'interface de bureau SYNAPSE : l'hôte natif Rust sous Tauri v2, l'interface React 18, la gestion d'état Zustand et le pont IPC Stdio JSON-RPC sans ouverture de port réseau.

⬅️ [Hub de Documentation](README.md) | ⚡ [Ingestion et HFT](data_ingestion_and_hft.md) | 🛡️ [Sécurité et Watchdog](safety_and_watchdog.md)

---

## 1. Vue d'Ensemble et Sécurité Zero-Port

Pour se conformer aux exigences de sécurité des centres de régulation du trafic, SYNAPSE n'expose aucun port HTTP ou WebSocket sur la machine locale. La communication entre l'interface utilisateur et le backend Python emprunte des tubes anonymes d'E/S standard avec des messages JSON-RPC délimités par des sauts de ligne :

```
┌────────────────────────────────────────────────────────┐
│               APPLICATION DESKTOP TAURI v2             │
│                                                        │
│   ┌────────────────────────────────────────────────┐   │
│   │                 REACT 18 SPA                   │   │
│   │  - Magasins Réactifs Zustand                   │   │
│   │  - Tailwind CSS + Icônes Lucide                │   │
│   │  - Visualisations en Temps Réel ECharts        │   │
│   └───────────────────────┬────────────────────────┘   │
│                           │ Commandes Invoke Tauri     │
│   ┌───────────────────────▼────────────────────────┐   │
│   │               RUST CORE (src-tauri)            │   │
│   │  - Gestionnaire de Processus Fils (Python)     │   │
│   │  - Intercepteur Asynchrone de Tubes Stdio      │   │
│   └───────────────────────┬────────────────────────┘   │
└───────────────────────────┼────────────────────────────┘
                            │ STDIN / STDOUT (JSON-RPC)
┌───────────────────────────▼────────────────────────────┐
│              BACKEND PYTHON (StdioDaemon)              │
│  - CommandRouter, IpcEventBridge, Moteur PyTorch       │
└────────────────────────────────────────────────────────┘
```

---

## 2. Gestion Réactive de l'État (Stores Zustand)

L'interface s'articule autour de magasins d'état modulaires **Zustand** :

- **`useSensorsStore`** : Suivi des capteurs actifs, débit de paquets, scores de confiance Bayésiens et statuts (`ACTIVE`, `QUARANTINE`, `FALLBACK`).
- **`useTopologyStore`** : Gestion du graphe routier ($V, E$), géométrie spatiale et capacités de trafic.
- **`useSystemStore`** : Télémétrie CPU/GPU, charge VRAM, temps de cycle d'inférence ($< 15\text{ ms}$) et supervision F.E.N.I.X.
- **`useXaiStore`** : Stockage des avis d'experts rédigés par Qwen3 Jurist et historique des alertes.

---

## 3. Protocole IPC Stdio JSON-RPC

Les échanges s'effectuent selon la norme JSON-RPC 2.0 asynchrone :

### Exemple de Requête (UI $\rightarrow$ Python) :
```json
{
  "jsonrpc": "2.0",
  "id": "req-1042",
  "method": "get_topology_snapshot",
  "params": {
    "include_metrics": true
  }
}
```

### Exemple d'Événement Émis (Python $\rightarrow$ UI via STDOUT) :
```json
{
  "jsonrpc": "2.0",
  "method": "on_telemetry_tick",
  "params": {
    "timestamp_ns": 1774728190000000,
    "active_sensors": 48,
    "mean_trust_score": 0.942,
    "hft_latency_ms": 1.2
  }
}
```

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
