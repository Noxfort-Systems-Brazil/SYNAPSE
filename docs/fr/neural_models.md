# 🧠 SYNAPSE: Stack Neuronal MARKVART™ et Formulations Mathématiques

Ce document expose les formulations mathématiques rigoureuses, fonctions de perte et spécifications d'opérateurs PyTorch des 10 réseaux de neurones et du moteur déterministe composant l'écosystème **MARKVART™** (Modular Adaptive Reasoning Kernel with Variational Attention & Recurrent Transformers).

⬅️ [Hub de Documentation](README.md) | 🗂️ [Entités de Domaine](domain_entities.md) | ⏱️ [Phases d'Exécution](execution_phases.md)

---

## 1. Taxonomie Opérationnelle MARKVART™

Les 10 modèles neuronaux et le moteur d'indexation spatiale déterministe fonctionnent de concert sur trois niveaux complémentaires :

| Modèle | Sous-système / Agent | Paradigme Mathématique | Rôle Principal |
|:---|:---|:---|:---|
| **PINO-Traffic** | Opérateur Continu | Opérateur Neural de Fourier (FNO) + EDP LWR | Simulation de densité continue et ondes de choc. |
| **PI-DeepONet** | Estimateur de Champs | Réseau Dual Branch-Trunk d'Opérateurs | Approximation non-linéaire des champs de vitesse. |
| **iTransformer** | Fusion Multivariée | Attention par Inversion Temporelle des Tokens | Fusion spatiale multi-capteurs sans diaphonie de canaux. |
| **GATv2 Lite** | Raisonnement Graphe | Attention Dynamique Spatio-Temporelle | Propagation de la congestion entre intersections voisines. |
| **WaveletAE-OCC**| Filtrage d'Anomalies | Ondelettes Discrètes (DWT) + Auto-encodeur | Détection de perturbations haute fréquence et cyberattaques. |
| **PatchTST** | Prévision par Patchs | Découpage Temporel + Attention Indépendante | Projection multi-horizons des vitesses et taux d'occupation. |
| **TCNAE** | Compression Latente | Convolutions Causales Dilatées 1D + Portes | Représentation compacte des séries de capteurs au sol. |
| **TimesNet** | Périodicité Urbaine | Décomposition 2D Fourier + Blocs Inception | Capture des cycles diurnes et hebdomadaires de trafic. |
| **FastMapMatcher** | Alignement Spatial | Indexation Spatiale R-Tree + Distance Fréchet (CPU) | Résolution déterministe sub-microseconde des écarts géospatiaux entre polylignes externes et réseau SUMO. |
| **PI-DVAE-TCN** | Estimation d'Incertitude| Auto-encodeur Variationnel sous Contraintes | Quantification des incertitudes épistémiques et aléatoires. |
| **Qwen3 Jurist** | Justification Cognitive| Petit Modèle de Langage (SLM) GGUF 4-bit | Synthèse de justifications textuelles et rapports d'audit. |

---

## 2. Opérateurs Neuronaux Guidés par la Physique

### PINO-Traffic (Physics-Informed Neural Operator)
- **Module** : `src/models/pino_traffic.py`
- **Loi Fondamentale** : Équation aux Dérivées Partielles de Lighthill-Whitham-Richards (LWR) :

$$\frac{\partial \rho}{\partial t} + \frac{\partial (\rho \cdot v)}{\partial x} = 0, \quad v(\rho) = v_f \left(1 - \frac{\rho}{\rho_{\text{jam}}}\right)$$

#### Fonction de Perte Résiduelle Physique :
$$\mathcal{L}_{\text{PINO}} = \mathcal{L}_{\text{données}} + \lambda_{\text{pde}} \mathcal{L}_{\text{pde}} + \lambda_{\text{ic}} \mathcal{L}_{\text{ic}}$$

$$\mathcal{L}_{\text{pde}} = \left\| \frac{\partial \rho_{\theta}}{\partial t} + \frac{\partial}{\partial x}\left(\rho_{\theta} \cdot v(\rho_{\theta})\right) \right\|_{L^2}^2$$

### PI-DeepONet (Approximation Continue d'Opérateurs)
- **Module** : `src/models/pi_deeponet.py`
- Projette les conditions limites via un réseau **Branch** $b(u)$ et les coordonnées via un réseau **Trunk** $t(y)$ :

$$G_{\theta}(u)(y) \approx \sum_{k=1}^P b_k(u) \cdot t_k(y) + b_0$$

---

## 3. Fusion Spatio-Temporelle Avancée

### iTransformer (Attention Inversée)
- **Module** : `src/models/itransformer.py`
Projette la série temporelle complète de chaque capteur sous forme d'un token individuel :

$$\mathbf{H}_i = \text{Embedding}(\mathbf{X}_{:, i}) \in \mathbb{R}^D$$

$$\mathbf{Z} = \text{Softmax}\left(\frac{\mathbf{Q}\mathbf{K}^T}{\sqrt{D}}\right)\mathbf{V}$$

### GATv2 Lite (Attention Dynamique sur Graphe)
- **Module** : `src/models/gatv2_lite.py`
Calcule dynamiquement les coefficients d'attention entre tronçons routiers adjacents :

$$\alpha_{ij} = \frac{\exp\left(\mathbf{a}^T \text{LeakyReLU}\left(\mathbf{W}_1 \mathbf{h}_i + \mathbf{W}_2 \mathbf{h}_j\right)\right)}{\sum_{k \in \mathcal{N}(i)} \exp\left(\mathbf{a}^T \text{LeakyReLU}\left(\mathbf{W}_1 \mathbf{h}_i + \mathbf{W}_2 \mathbf{h}_k\right)\right)}$$

---

## 4. Justification Légale et Audit avec Qwen3 Jurist

Le modèle **Qwen3 Jurist** est exécuté en local sans connexion internet via llama.cpp (quantification 4 bits GGUF), produisant des rapports techniques justifiant les déclenchements d'alerte ou les recommandations de modification de phase.

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
