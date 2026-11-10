# 🧠 SYNAPSE: MARKVART™ Neural Stack & Mathematical Formulations

This document provides exhaustive mathematical formulations, loss functions, and PyTorch operator specifications for the 10 neural networks and deterministic spatial engine comprising the **MARKVART™** (Modular Adaptive Reasoning Kernel with Variational Attention & Recurrent Transformers) ecosystem.

⬅️ [Documentation Hub](README.md) | 🗂️ [Domain Entities](domain_entities.md) | ⏱️ [Execution Phases](execution_phases.md)

---

## 1. MARKVART™ Functional Taxonomy

The 10 neural models and deterministic spatial indexing engine operate across three synergistic tiers:

| Model | Subsystem / Agent | Mathematical Formulation / Paradigm | Primary Responsibility |
|:---|:---|:---|:---|
| **PINO-Traffic** | Continuum Operator | Fourier Neural Operator (FNO) + LWR Conservation PDE | Macroscopic density simulation & shockwave propagation. |
| **PI-DeepONet** | Field Estimator & Imputer | Dual Branch-Trunk Deep Operator Network | Infinite-dimensional non-linear mapping of velocity fields & gap imputation. |
| **iTransformer** | Multivariate Fusion | Inverted Dimension Attention over Time Tokens | Cross-sensor spatial fusion without channel mixing artifacts. |
| **GATv2 Lite / DiffusionGATv2** | Graph Reasoning | Dynamic Attention with 5D Physical Edge Tensor (`edge_attr`) + Harmonic Diffusion | Propagates congestion across neighboring nodes weighted by physical conductance and road hierarchy. |
| **WaveletAE-OCC**| Anomaly Gatekeeper | Discrete Wavelet Transform (DWT) + One-Class Autoencoder | High-frequency sensor glitch & tampering detection. |
| **ModernBERT & NeuroSymbolic** | Semantic Gatekeeper | ModernBERT Backbone + Decoupled TCNAE + 3D Physics Head | Zero-trust validation of sensor schemas with LWR conservation loss penalties. |
| **TCNAE** | Latent Compression | Dilated Causal 1D Convolutions with Residual Gates | Compact representation of raw loop sensor series. |
| **SpectralFeatureBlock** | Periodicity Engine | 1D Fourier Spectral Convolutions (`SpectralConv1d`) | Captures diurnal and seasonal traffic periodicity (optimized TimesNet drop-in). |
| **FastMapMatcher** | Spatial Alignment | R-Tree Spatial Index + Fréchet Distance (CPU) | Resolves spatial misalignments between multi-segment Waze/TomTom `jams` polylines and SUMO street topology in sub-microseconds. |
| **PI-DVAE-TCN** | Uncertainty Estimator | Physics-Constrained Variational Autoencoder | Quantifies epistemic and aleatoric sensor uncertainties. |
| **Qwen3 Jurist** | Cognitive Justifier| Quantized GGUF Small Language Model (SLM) with Out-of-Process Isolation | Generates audit-compliant textual justifications without blocking PyTorch threads. |

---

## 2. Continuum Physics Operators

### PINO-Traffic (Physics-Informed Neural Operator)
- **Module**: `src/models/pino_traffic.py`
- **Governing Law**: Lighthill-Whitham-Richards (LWR) conservation PDE:

$$\frac{\partial \rho}{\partial t} + \frac{\partial (\rho \cdot v)}{\partial x} = 0, \quad v(\rho) = v_f \left(1 - \frac{\rho}{\rho_{\text{jam}}}\right)$$

#### Physics-Informed Loss Function:
$$\mathcal{L}_{\text{PINO}} = \mathcal{L}_{\text{data}} + \lambda_{\text{pde}} \mathcal{L}_{\text{pde}} + \lambda_{\text{ic}} \mathcal{L}_{\text{ic}}$$

$$\mathcal{L}_{\text{pde}} = \left\| \frac{\partial \rho_{\theta}}{\partial t} + \frac{\partial}{\partial x}\left(\rho_{\theta} \cdot v(\rho_{\theta})\right) \right\|_{L^2}^2$$

### PI-DeepONet (Operator Field Approximator)
- **Module**: `src/models/pi_deeponet.py`
- Formulates input boundary conditions via a **Branch Network** $b(u)$ and continuous spatiotemporal query points via a **Trunk Network** $t(y)$:

$$G_{\theta}(u)(y) \approx \sum_{k=1}^P b_k(u) \cdot t_k(y) + b_0$$

---

## 3. High-Performance Spatial & Temporal Fusion

### iTransformer (Inverted Token Attention)
- **Module**: `src/models/itransformer.py`
Unlike traditional Transformers that embed all channels at a single time step as a token, **iTransformer** embeds the entire temporal sequence of an individual sensor as a distinct token:

$$\mathbf{H}_i = \text{Embedding}(\mathbf{X}_{:, i}) \in \mathbb{R}^D$$

$$\mathbf{Z} = \text{Softmax}\left(\frac{\mathbf{Q}\mathbf{K}^T}{\sqrt{D}}\right)\mathbf{V}$$

This guarantees that spatial correlations across disparate sensors are modeled through global multi-head self-attention without inter-channel entanglement.

### GATv2 Lite & DiffusionGATv2 (Physical Spatiotemporal Graph Attention)
- **Modules**: `src/models/gatv2_lite.py`, `src/models/diffusion_gatv2.py`
Dynamically adjusts attention weights across connected roadway segments incorporating the 5D physical edge tensor ($\mathbf{e}_{ij} \in \mathbb{R}^{E \times 5}$: normalized length, free-flow speed, lane count, road hierarchy/priority, and physical conductance):

$$\alpha_{ij} = \frac{\exp\left(\mathbf{a}^T \text{LeakyReLU}\left(\mathbf{W}_1 \mathbf{h}_i + \mathbf{W}_2 \mathbf{h}_j + \mathbf{W}_e \mathbf{e}_{ij}\right)\right)}{\sum_{k \in \mathcal{N}(i)} \exp\left(\mathbf{a}^T \text{LeakyReLU}\left(\mathbf{W}_1 \mathbf{h}_i + \mathbf{W}_2 \mathbf{h}_k + \mathbf{W}_e \mathbf{e}_{ik}\right)\right)}$$

In `FusionPipeline`, unobserved nodes ($M_i = 0$) are reconstructed by blending the `DiffusionGATv2` projection with an **8-hop damped harmonic graph diffusion** weighted by physical conductance and anchored to a topological prior (`y_bg`), eliminating spatial flatness across sparse sensor deployments.

---

## 4. Semantic Gatekeeping & Textual Explainability
 
- **ModernBERT & NeuroSymbolicModel (`src/models/modernbert.py`, `src/models/neuro_symbolic.py`)**: Combines a high-throughput ModernBERT transformer backbone (with Tensor Core acceleration, `allow_tf32 = True`) with a decoupled `TCNAE` and a 3D Physics Projection Head $\mathbf{y}_{\text{phys}} = [q, v, \rho]$. Feeds physical states through LWR continuum equations and penalizes schema deviations before promoting quarantined data sources.
- **WaveletAE-OCC (`src/models/wavelet_ae_occ.py`)**: Decomposes high-frequency raw telemetry using Daubechies Wavelets ($\psi_{j, k}$) to isolate impulse noise and cyber-attacks before tensor ingestion.
- **Qwen3 Jurist (`src/agents/jurist_agent.py`, `src/slm/`)**: Operates strictly on local GPU/CPU via quantized GGUF/SafeTensors models. Isolated in a dedicated background worker process (`src/slm/process/isolated_jurist_manager.py`) to guarantee that generative SLM latency never degrades the sub-250ms real-time PyTorch inference cycle. Formulates forensically defensible textual statements and mathematical derivations in 6 languages.

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
