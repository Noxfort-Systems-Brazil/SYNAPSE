# 🧪 SYNAPSE: Directives de Test et Assurance Qualité

Ce document présente l'infrastructure de tests automatisés, les suites Pytest, les générateurs de trafic synthétique et les métriques de couverture du code pour **SYNAPSE CORE**.

⬅️ [Hub de Documentation](README.md) | 🛡️ [Sécurité et Watchdog](safety_and_watchdog.md) | 🏛️ [Architecture Système](architecture.md)

---

## 1. Organisation des Suites de Tests

L'ensemble des tests est regroupé sous le répertoire `tests/` :

- **Tests Unitaires (`tests/unit/`)** : Validation isolée des entités de domaine, calculs cinématiques et transitions d'états.
- **Tests des Réseaux Neuronaux (`tests/models/`)** : Vérification des passes avant/arrière (forward/backward), dimensions des tenseurs et stabilité des gradients pour les 11 modèles MARKVART™.
- **Tests d'Intégration (`tests/integration/`)** : Validation du flux complet depuis les adaptateurs d'ingestion jusqu'à l'émission gRPC.
- **Tests IPC (`tests/ipc/`)** : Évaluation de la robustesse du protocole JSON-RPC Stdio face à des flux saturés et des messages malformés.
- **Benchmarks (`tests/benchmarks/`)** : Mesure des temps de cycle d'inférence, de la consommation mémoire et des débits de sérialisation.

---

## 2. Exécution des Tests

Activez l'environnement virtuel avant toute exécution :

```bash
source .venv/bin/activate
```

### Lancer la Totalité des Tests Pytest :
```bash
pytest tests/ -v
```

### Lancer avec Rapport de Couverture de Code :
```bash
pytest --cov=src --cov-report=term-missing --cov-report=html tests/
```

### Lancer Exclusivement les Modèles Neuronaux :
```bash
pytest tests/test_neural_models.py -v
```

---

## 3. Données Synthétiques et Mocks Déterministes

Pour autoriser les tests dans des environnements isolés sans liaison physique avec le terrain :

- **`SyntheticTrafficGenerator`** : Modélise les flux de véhicules et la propagation d'ondes de choc selon les équations de Greenshields.
- **`MockHftReceiver`** : Serveur gRPC simulé en mémoire pour vérifier la conformité du protocole et la latence.
- **Graines Aléatoires Fixées** : Toutes les suites initialisent des graines constantes (`torch.manual_seed(42)`) afin d'assurer une reproductibilité numérique parfaite.

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
