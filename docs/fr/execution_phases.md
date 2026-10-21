# ⏱️ SYNAPSE: Phases d'Exécution ADAGIO™ et Cinématique KSE

Ce document décrit le cycle de vie de la plateforme **ADAGIO™** (Adaptive Distributed Autonomous Graph Ingestion & Optimization) et le module d'extrapolation cinématique par filtre de Kalman **KSE** (Kinematic State Estimation).

⬅️ [Hub de Documentation](README.md) | 🧠 [Stack Neuronal MARKVART™](neural_models.md) | ⚡ [Ingestion et HFT](data_ingestion_and_hft.md)

---

## 1. Progression des Phases ADAGIO™

SYNAPSE structure ses opérations à travers trois phases séquentielles strictes :

```
┌────────────────────────────────┐
│   Phase 0 : Optimisation AutoML│  ◄── Recherche Bayésienne d'hyperparamètres (Optuna)
└───────────────┬────────────────┘
                │ Convergence des hyperparamètres optimaux
┌───────────────▼────────────────┐
│   Phase 1 : Bootstrap Doré     │  ◄── Ingestion des journaux historiques et étalonnage
└───────────────┬────────────────┘
                │ Validation anti-corruption Ghost-File
┌───────────────▼────────────────┐
│   Phase 2 : Runtime 4-Threads  │  ◄── Boucle temps réel avec 4 threads dédiés
└────────────────────────────────┘
```

### Phase 0 : Optimisation AutoML
- Explore l'espace des hyperparamètres des réseaux MARKVART™ via **Optuna** : taux d'apprentissage, modes spectraux FNO ($k_{\max} \in [8, 32]$) et têtes d'attention GATv2.
- Élimine les configurations divergentes de manière précoce à l'aide d'élagueurs statistiques (`MedianPruner`).

### Phase 1 : Bootstrap du Dataset Doré (Golden Dataset)
- Traite les historiques de trafic municipaux, la cartographie OpenStreetMap et les boucles électromagnétiques.
- Produit des tenseurs consolidés et physiquement valides (**Dataset Doré**).
- **Protection Ghost-File** : Écriture atomique dans des fichiers temporaires avec contrôle SHA-256 préalable pour prévenir toute corruption lors des arrêts inattendus.

### Phase 2 : Runtime Multithread Concurrent
Le moteur opérationnel exécute quatre threads asynchrones non-bloquants :

1. **Thread d'Ingestion** : Écoute les protocoles HTTP/MQTT/WebSocket et valide les indices de confiance Bayésiens.
2. **Thread Cinématique (KSE)** : Extrapole les coordonnées et vitesses par filtre de Kalman lors de pertes de paquets.
3. **Thread d'Inférence Neuronale** : Exécute les modèles MARKVART™ sur GPU via des CUDA Streams (PINO, GATv2, iTransformer).
4. **Thread de Streaming HFT** : Sérialise les matrices de densité en Protobuf et les pousse via gRPC vers CARINA.

---

## 2. Extrapolation Cinématique (KSE) Dead Reckoning

En cas d'interruption temporaire des transmissions capteurs, le module **KSE Dead Reckoning** prend le relais :

### Vecteur d'État du Filtre de Kalman Discret
$$\mathbf{x}_k = \begin{bmatrix} s_k \\ v_k \\ a_k \end{bmatrix}$$

Où $s_k$ est la position sur le segment, $v_k$ la vitesse et $a_k$ l'accélération.

### Modèle de Transition :
$$\mathbf{x}_{k+1} = \mathbf{F} \mathbf{x}_k + \mathbf{w}_k$$

$$\mathbf{F} = \begin{bmatrix} 1 & \Delta t & \frac{1}{2}\Delta t^2 \\ 0 & 1 & \Delta t \\ 0 & 0 & 1 \end{bmatrix}, \quad \mathbf{w}_k \sim \mathcal{N}(0, \mathbf{Q})$$

Si un capteur reste silencieux pendant $N_{\text{missed}} \ge 3$ cycles successifs, l'état cinématique estimé compense le manque de données et rétrograde le statut de la source à `FALLBACK`.

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
