# 🛡️ SYNAPSE: Sécurité, Watchdog et Politique de Repli

Ce document détaille les règles neuro-symboliques de sécurité, le superviseur indépendant **F.E.N.I.X.**, le contrôle de présence par signaux de vie (heartbeats), la gestion de la mémoire et la politique de dégradation douce (**Gating Policy**).

⬅️ [Hub de Documentation](README.md) | 🖥️ [Interface Desktop](ui_architecture.md) | 🧪 [Tests et QA](testing.md)

---

## 1. Superviseur Indépendant F.E.N.I.X.

Afin de garantir un fonctionnement continu en infrastructure critique, le moteur d'IA opère sous le contrôle d'un superviseur distinct (`src/fenix/process_supervisor.py`) :

```bash
python synapse.py --supervisor
```

### Missions Fondamentales :
1. **Pulsations Cardiaques (Heartbeats)** : Le processus d'inférence transmet des battements toutes les 250 ms. L'absence de signal pendant plus de **500 ms** déclenche un diagnostic de blocage.
2. **Plafonnement Mémoire** : Le superviseur scrute l'empreinte RSS. Si elle excède la limite définie (ex. 4096 Mo), il déclenche un ramasse-miettes forcé ou un redémarrage fluide du processus.
3. **Résurrection Automatique** : Lors d'un défaut de segmentation ou d'une erreur CUDA out-of-memory, F.E.N.I.X. relance une instance saine en **moins de 1,0 s** en réinjectant le dernier état validé.

---

## 2. Politique de Dégradation Douce (Gating Policy)

En cas d'altération ou de défaillance des liaisons de communication, la **Gating Policy** (`src/domain/gating_policy.py`) empêche toute propagation de valeurs nulles :

```
┌────────────────────────────────────────────────────────┐
│             CASCADE DE LA GATING POLICY                │
│                                                        │
│  [Niveau 1 : Perception Neuronale Complète]            │
│  Inférence MARKVART™ sur les capteurs actifs valides   │
│                           │                            │
│                           ▼ (Perte ponctuelle de paquets)
│  [Niveau 2 : Extrapolation Cinématique (KSE)]          │
│  Calcul continu par Filtre de Kalman (v, a)            │
│                           │                            │
│                           ▼ (> 30s d'interruption)     │
│  [Niveau 3 : Profils Historiques (MEH)]                │
│  Injection de modèles statistiques horaires            │
└────────────────────────────────────────────────────────┘
```

- **Niveau 1 (Neuronal)** : Fonctionnement nominal avec score de confiance $\tau \ge 0.70$.
- **Niveau 2 (KSE)** : S'enclenche dès les premières pertes de paquets ($1 \le N_{\text{missed}} \le 30$).
- **Niveau 3 (Historique)** : S'active lors de coupures prolongées du matériel de terrain.

---

## 3. Invariants Physiques Symboliques

Les paquets de données sont soumis à des filtres de validation physique stricts :
- **`SR-01 (Vitesse Maximale)`** : $v \le 180\text{ km/h}$ en milieu urbain.
- **`SR-02 (Invariant d'Accélération)`** : $|a| \le 8.5\text{ m/s}^2$ (limites dynamiques de décélération).
- **`SR-03 (Densité Maximale)`** : $\rho \le \rho_{\text{jam}} = 140\text{ véh/km/voie}$.
- **`SR-04 (Conservation des Flux)`** : Cohérence des équilibres volumétriques aux intersections.

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
