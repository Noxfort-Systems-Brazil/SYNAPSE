# 03. Neural Models & PyTorch Implementations (MARKVART™)

> **Complete Mathematical Formulations, Loss Functions, and PyTorch Operators of the 10 MARKVART™ Neural Architectures & Deterministic Spatial Engine**

---

> 🧭 **Navigation**:
> [🏠 Synapse Core](../README.md) • [📚 Docs Index](README.md) • [« Previous: 02. UI Architecture](02_ui_architecture.md) • [Next: 04. Execution Phases »](04_execution_phases.md)

---

## 🧠 Overview: MARKVART™ Neural Architecture

The **Modular Adaptive Reasoning Kernel with Variational Attention & Recurrent Transformers (MARKVART™)** deploys an ensemble of 10 deep neural architectures alongside a deterministic spatial indexing engine across three operational layers:
1. **Perception & Semantic Gatekeeping**: Ingestion filtering, schema understanding, and anomaly detection.
2. **Local Kinematics & Topology**: Edge-level feature extraction, deterministic geometric map matching, and graph spatial attention.
3. **Continuum Physics & Global Fusion**: Infinite-dimensional macroscopic flow modeling, operator learning, and explainable AI generation.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MARKVART™ NEURAL STACK                             │
│                                                                             │
│  [Ingestion & Gatekeeping]   ModernBERT + NeuroSymbolic │  WaveletAE-OCC     │
│  [Local Representation]      TCNAE                      │  PI-DeepONet       │
│  [Spatial Reasoning]         GATv2 Lite                 │  FastMapMatcher    │
│  [Temporal Periodicity]      SpectralFeatureBlock       │  PI-DVAE-TCN       │
│  [Continuum Operators]       PINO-Traffic               │  PI-DeepONet       │
│  [Global Fusion & XAI]       iTransformer               │  Qwen3 Jurist(SLM) │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. PINO-Traffic (Physics-Informed Neural Operator)
- **Module**: [`src/models/pino_traffic.py`](../src/models/pino_traffic.py)
- **Agent**: `FuserAgent` / `ContinuumOperator`
- **Mathematical Paradigm**: Fourier Neural Operator (FNO) constrained by the Lighthill-Whitham-Richards (LWR) Partial Differential Equation (PDE):

$$\frac{\partial \rho}{\partial t} + \frac{\partial (\rho \cdot v)}{\partial x} = 0, \quad q = \rho \cdot v(\rho)$$

Where:
- $\rho(x, t)$ is vehicle density (veh/km).
- $v(\rho) = v_f \left(1 - \frac{\rho}{\rho_{\text{jam}}}\right)$ is the Greenshields velocity model.
- $q(x, t)$ is macroscopic vehicle flow rate (veh/h).

### Physics Residual Loss
$$\mathcal{L}_{\text{PINO}} = \mathcal{L}_{\text{data}} + \lambda_{\text{pde}} \mathcal{L}_{\text{pde}} + \lambda_{\text{ic}} \mathcal{L}_{\text{initial}}$$

$$\mathcal{L}_{\text{pde}} = \left\| \frac{\partial \rho_{\theta}}{\partial t} + \frac{\partial}{\partial x} \left( \rho_{\theta} \cdot v(\rho_{\theta}) \right) \right\|_{L^2}^2$$

The spectral convolution operates directly in the spatial frequency domain using 1D/2D Fast Fourier Transforms (FFT), enabling zero-shot super-resolution across road segments regardless of grid discretization.

---

## 2. PI-DeepONet (Continuous Spatio-Temporal Field Estimator)
- **Module**: [`src/models/pi_deeponet.py`](../src/models/pi_deeponet.py)
- **Mathematical Paradigm**: Dual-network Branch/Trunk Deep Operator Network (Lu et al., 2021).

$$G_{\theta}(u)(y) \approx \sum_{k=1}^P b_k(u) \cdot t_k(y) + b_0$$

Where:
- **Branch Network $b_k(u)$**: Ingests discrete historical sensor telemetry $u = [u(x_1), \dots, u(x_m)]$.
- **Trunk Network $t_k(y)$**: Ingests continuous spatio-temporal query coordinates $y = (x, t)$.
- **Scalar Product $\sum b_k t_k$**: Yields the continuous velocity field $v(x, t)$ at arbitrary coordinates between physical sensors.

---

## 3. PI-DVAE-TCN (Physics-Informed Denoising Autoencoder)
- **Module**: [`src/models/pi_dvae_tcn.py`](../src/models/pi_dvae_tcn.py)
- **Agent**: `CorrectorAgent`
- **Architecture**: Dilated Causal 1D Convolutions combined with a Variational Autoencoder ($q_{\phi}(z|x)$, $p_{\theta}(x|z)$).
- **Kinetic Conservation Penalty**:
  $$\mathcal{L}_{\text{DVAE}} = \mathbb{E}_{q_{\phi}(z|x)}[\log p_{\theta}(x|z)] - \beta D_{\text{KL}}(q_{\phi}(z|x) \parallel p(z)) - \gamma \left\| \frac{d^2 x_{\text{recon}}}{dt^2} - a_{\text{max}} \right\|_+$$
  Penalizes non-physical vehicle acceleration spikes exceeding physical engine brake capabilities ($> 8\text{ m/s}^2$).

---

## 4. iTransformer (Global Multivariate Fusion)
- **Module**: [`src/models/itransformer.py`](../src/models/itransformer.py)
- **Agent**: `FuserAgent`
- **Architectural Inversion**:
  Instead of standard time-step tokens ($T$ tokens of size $N$), the iTransformer forms $N$ tokens of size $T$. **Each token represents a single sensor's complete temporal trajectory**.
- **Cross-Sensor Attention**:
  $$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_{\text{model}}}}\right)V$$
  Because tokens are sensors, the self-attention matrix natively captures inter-sensor mutual dependencies without temporal overfitting.
- **Pred Length**: Tuned with `pred_len=1` to reconstruct the synchronized present state ($t_0$) filtering out asynchronous network delays.

---

## 5. GATv2 Lite & Diffusion GATv2 (Topological Reasoning)
- **Module**: [`src/models/gatv2_lite.py`](../src/models/gatv2_lite.py), [`src/models/diffusion_gatv2.py`](../src/models/diffusion_gatv2.py)
- **Agent**: `CoordinatorAgent` / `FusionPipeline`
- **Dynamic Attention Formulation with 5D Physical Edge Attributes**:
  $$e(h_i, h_j, \mathbf{e}_{ij}) = \mathbf{a}^T \text{LeakyReLU}\left(\mathbf{W} \cdot [h_i \parallel h_j \parallel \mathbf{W}_e \mathbf{e}_{ij}]\right)$$
  $$\alpha_{ij} = \frac{\exp(e(h_i, h_j, \mathbf{e}_{ij}))}{\sum_{k \in \mathcal{N}_i} \exp(e(h_i, h_k, \mathbf{e}_{ik}))}$$
  - **5D Physical Edge Vector ($\mathbf{e}_{ij} \in \mathbb{R}^{E \times 5}$)**: Extracted directly from SUMO `.net.xml.gz` topology via `GraphTopologyService.get_edge_index()`, encoding normalized segment length, free-flow speed ($v_{\max}$), lane count, road hierarchy/priority (`highway.primary`, `secondary`, `tertiary`, `residential`, `living_street`), and macroscopic conductance ($C_{ij} = \text{lanes} \cdot v_{\max} \cdot w_{\text{type}} / L$).
  - **8-Hop Damped Harmonic Graph Diffusion**: In `FusionPipeline`, unobserved nodes ($M_i = 0$) are reconstructed by combining the `DiffusionGATv2` neural projection with an 8-hop conductance-weighted harmonic propagation anchored at observed sensors ($M_i = 1$) and regularized toward a topological prior (`y_bg`), eliminating spatial flatness across sparse sensor deployments.

---

## 6. Fast Geometric Map Matching (Deterministic R-Tree + Fréchet)
- **Module**: [`src/services/fast_map_matcher.py`](../src/services/fast_map_matcher.py)
- **Subsystem**: `GlobalCartographerMatcher` (Linguist Layer) & `GraphManager._ingest_global_jams_feed`
- **Geometric Continuum Alignment**:
  Replaces previous heavy neural map-matching with a zero-VRAM, ultra-low latency deterministic engine running entirely on CPU:
  - **R-Tree Spatial Index**: Filters candidate edges within the bounding radius in sub-microsecond time ($\mu s$).
  - **Fréchet & Hausdorff Metrics**: Computes exact geometric proximity between external polylines (Waze/TomTom) and SUMO centerline geometry.
  - **Multi-Segment Global Jam Unpacking**: When global traffic APIs emit multi-segment `jams` arrays (`line: [{x, y}, ...]`), `GraphManager._ingest_global_jams_feed` projects each jam's WGS84 polyline into local meters via `GeoProjectionService`, matches it to its exact `MapEdge` via `FastMapMatcher`, updates `edge.jam_Translation["waze_jam"]` (`speed_kmh`, `jam_level`, `delay_s`, `length_m`), and automatically clears expired jams from previously affected edges.
  - **Directional Vector Disambiguation**: Resolves opposite and parallel lanes deterministically with 100% test reproducibility, zero GPU allocation, and no Optuna hyperparameter calibration overhead.

---

## 7. SpectralFeatureBlock (Multi-Period Frequency Decomposition)
- **Module**: [`src/blocks/feature_blocks.py`](../src/blocks/feature_blocks.py), [`src/blocks/spectral_blocks.py`](../src/blocks/spectral_blocks.py)
- **Agent**: `TranslationAgent`, `PeakClassifierAgent`
- **Fourier Spectral Feature Extraction**:
  Acts as an optimized drop-in replacement for TimesNet in `PeakClassifierAgent` and `PeakPipeline`. Applies 1D Fast Fourier Convolutions (`SpectralConv1d`) across multi-scale frequency bands to extract periodic patterns:
  $$A = \text{FFT}(X), \quad f_1, \dots, f_k = \text{argtopk}(|A|)$$
  Processes intraday (rush hour) and intraweek (weekend dip) periodic patterns, feeding spectral representations into GMM temporal clustering.

---

## 8. PI-DeepONet (Continuous Operator Gap Imputation)
- **Module**: [`src/models/pi_deeponet.py`](../src/models/pi_deeponet.py), [`src/pipeline/imputer_pipeline.py`](../src/pipeline/imputer_pipeline.py)
- **Agent**: `ImputerAgent`
- **Infinite-Dimensional Field Reconstruction**:
  Instead of discrete autoregressive patching, the `ImputerPipeline` leverages `PIDeepONet` with sliding-window chunking and Z-score normalization (`TensorNormalizer`).
  - Evaluates non-linear continuous operators to reconstruct missing traffic telemetry during prolonged sensor outages ($> 2\text{ hours}$).
  - Guarantees smooth, physically sound velocity/density interpolations across temporal gaps without compounding cumulative errors.

---

## 9. WaveletAE-OCC (High-Frequency Anomaly Detector)
- **Module**: [`src/models/wavelet_ae_occ.py`](../src/models/wavelet_ae_occ.py)
- **Agent**: `AuditorAgent`
- **Wavelet Scattering + Deep SVDD**:
  Uses Discrete Wavelet Transforms (DWT) to split signals into frequency octaves. The Autoencoder maps normal urban flow into a minimum-volume hypersphere in latent space:
  $$\min_{W} R^2 + \frac{1}{\nu N} \sum_{i=1}^N \max(0, \|\phi(x_i; W) - c\|^2 - R^2)$$
  Readings exceeding the $\mu + 3\sigma$ threshold trigger the Jurist Agent.

---

## 10. ModernBERT & NeuroSymbolicModel (Zero-Trust Semantic Gatekeeping)
- **Module**: [`src/models/modernbert.py`](../src/models/modernbert.py), [`src/models/neuro_symbolic.py`](../src/models/neuro_symbolic.py)
- **Agent**: `LinguistAgent`, `PeakClassifierAgent`
- **Neuro-Symbolic Architecture & Tensor Core Acceleration**:
  - **ModernBert Backbone**: Fast transformer embedding model with native PyTorch SDPA attention and global Tensor Core acceleration (`allow_tf32 = True`). Extracts continuous semantic representations from heterogeneous sensor schemas.
  - **Decoupled TCNAE**: Temporal Convolutional Autoencoder compressing representations into a low-dimensional manifold.
  - **Physics Projection Head**: Translates latent embeddings directly into physical macroscopic traffic states:
    $$\mathbf{y}_{\text{phys}} = [q \text{ (flow)}, v \text{ (speed)}, \rho \text{ (density)}]$$
  - Constrained by the LWR continuum equation $q = \rho \cdot v(\rho)$ and Greenshields boundary parameters.
- **Assets**: Weights stored in [`Model_Vault/`](../Model_Vault/README.md).

---

## 11. Qwen3 (Explainable AI & Legal Jurist)
- **Module**: [`src/agents/jurist_agent.py`](../src/agents/jurist_agent.py), [`src/pipeline/jurist_pipeline.py`](../src/pipeline/jurist_pipeline.py), [`src/slm/`](../src/README.md)
- **Agent**: `JuristAgent`
- **Edge SLM Inference & Fault Isolation**:
  - Executes quantized 6-bit GGUF models (`Qwen3.5-2B-UD-Q6_K_XL.gguf` or SafeTensors) via `llama-cpp-python` with Zero Cloud API reliance.
  - **Out-of-Process Isolation**: Operates by default in a dedicated sub-process via `IsolatedJuristManager` (`src/slm/process/isolated_jurist_manager.py`), ensuring that memory spikes or LLM execution never interrupt real-time PyTorch inference threads.
- **Explainable AI (XAI)**:
  Synthesizes mathematical gradient attribution bars and writes natural language legal reports explaining neural sensor fusion attributions and telemetry integrity in 6 languages.
- **Assets**: Quantized binary in [`Model_Vault/`](../Model_Vault/README.md).

---

> 🧭 **Next Chapter**: Discover the ADAGIO™ execution pipeline in [04. Execution Phases & Lifecycle](04_execution_phases.md).

---

<div align="center">
  <img src="assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
