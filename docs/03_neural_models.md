# 03. Neural Models & PyTorch Implementations (MARKVART™)

> **Complete Mathematical Formulations, Loss Functions, and PyTorch Operators of the 11 MARKVART™ Neural Architectures**

---

> 🧭 **Navigation**:
> [🏠 Synapse Core](../README.md) • [📚 Docs Index](README.md) • [« Previous: 02. UI Architecture](02_ui_architecture.md) • [Next: 04. Execution Phases »](04_execution_phases.md)

---

## 🧠 Overview: MARKVART™ Neural Architecture

The **Modular Adaptive Reasoning Kernel with Variational Attention & Recurrent Transformers (MARKVART™)** deploys an ensemble of 11 deep neural architectures across three operational layers:
1. **Perception & Semantic Gatekeeping**: Ingestion filtering, schema understanding, and anomaly detection.
2. **Local Kinematics & Topology**: Edge-level feature extraction and graph spatial attention.
3. **Continuum Physics & Global Fusion**: Infinite-dimensional macroscopic flow modeling, operator learning, and explainable AI generation.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MARKVART™ NEURAL STACK                             │
│                                                                             │
│  [Ingestion & Gatekeeping]   DistilRoBERTa + GMM  │  WaveletAE-OCC          │
│  [Local Representation]      TCNAE                │  PatchTST               │
│  [Spatial Reasoning]         GATv2 Lite           │  Sinkhorn Cross-Attn    │
│  [Temporal Periodicity]      TimesNet             │  PI-DVAE-TCN            │
│  [Continuum Operators]       PINO-Traffic         │  PI-DeepONet            │
│  [Global Fusion & XAI]       iTransformer         │  Qwen3 Jurist (GGUF)    │
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
- **Agent**: `CoordinatorAgent`
- **Dynamic Attention Formulation**:
  $$e(h_i, h_j) = \mathbf{a}^T \text{LeakyReLU}\left(\mathbf{W} \cdot [h_i \parallel h_j]\right)$$
  $$\alpha_{ij} = \frac{\exp(e(h_i, h_j))}{\sum_{k \in \mathcal{N}_i} \exp(e(h_i, h_k))}$$
  Unlike static GATs, dynamic attention weights between road vertices vary as traffic conditions change (e.g., attending to upstream arterials exclusively during morning peak hours).

---

## 6. Sinkhorn Cross-Attention (Differentiable Map Matching)
- **Module**: [`src/models/sinkhorn_cross_attention.py`](../src/models/sinkhorn_cross_attention.py)
- **Agent**: `CartographerAgent`
- **Entropic Optimal Transport**:
  Solves the Kantorovich optimal transport problem aligning noisy GPS probe sequences $X \in \mathbb{R}^{M \times 2}$ to candidate street network edges $Y \in \mathbb{R}^{K \times 2}$:
  $$\min_{P \in U(r, c)} \langle P, C \rangle - \varepsilon H(P)$$
  Where $P$ is computed via iterative matrix scaling (Sinkhorn-Knopp algorithm) in $< 5\text{ ms}$ on GPU.

---

## 7. TimesNet (Multi-Period Frequency Decomposition)
- **Module**: [`src/models/timesnet.py`](../src/models/timesnet.py)
- **Agent**: `TranslationAgent`
- **FFT Periodicity Transform**:
  Transposes 1D time-series into 2D spatio-temporal representations based on top-$k$ frequency periods detected by 1D FFT:
  $$A = \text{FFT}(X), \quad f_1, \dots, f_k = \text{argtopk}(|A|)$$
  Processes intraday (rush hour) and intraweek (weekend dip) periodic patterns through 2D Inception blocks.

---

## 8. PatchTST (Long-Sequence Imputation)
- **Module**: [`src/models/patch_tst.py`](../src/models/patch_tst.py)
- **Agent**: `ImputerAgent`
- **Patch Extraction**:
  Splits continuous sensor signals into overlapping sub-patches of length $P$ with stride $S$:
  $$X_{\text{patch}} \in \mathbb{R}^{N \times P}$$
  Maintains temporal autocorrelation integrity during extended sensor outages ($> 2\text{ hours}$) without error accumulation.

---

## 9. WaveletAE-OCC (High-Frequency Anomaly Detector)
- **Module**: [`src/models/wavelet_ae_occ.py`](../src/models/wavelet_ae_occ.py)
- **Agent**: `AuditorAgent`
- **Wavelet Scattering + Deep SVDD**:
  Uses Discrete Wavelet Transforms (DWT) to split signals into frequency octaves. The Autoencoder maps normal urban flow into a minimum-volume hypersphere in latent space:
  $$\min_{W} R^2 + \frac{1}{\nu N} \sum_{i=1}^N \max(0, \|\phi(x_i; W) - c\|^2 - R^2)$$
  Readings exceeding the $\mu + 3\sigma$ threshold trigger the Jurist Agent.

---

## 10. DistilRoBERTa + GMM (Zero-Trust Linguist & Peak Scheduler)
- **Module**: [`src/models/distilroberta.py`](../src/models/distilroberta.py), [`src/models/neuro_symbolic.py`](../src/models/neuro_symbolic.py)
- **Agent**: `LinguistAgent`, `PeakClassifierAgent`
- **Semantic Schema Encoding**:
  Pre-trained transformer embeddings extract latent vectors from incoming raw JSON telemetry schemas. Unsupervised Gaussian Mixture Models (GMM) segment urban schedules into dynamic peak-hour regimes.
- **Assets**: Weights stored in [`Model_Vault/distilroberta/`](../Model_Vault/README.md).

---

## 11. Qwen3 (Explainable AI & Legal Jurist)
- **Module**: `src/agents/jurist_agent.py`, `src/prompts/`
- **Agent**: `JuristAgent`
- **Edge LLM Inference**:
  Executes quantized 6-bit GGUF models (`Qwen3.5-2B-UD-Q6_K_XL.gguf`) via `llama-cpp-python` with Zero Cloud API reliance.
- **Explainable AI (XAI)**:
  Synthesizes mathematical gradient attribution bars and writes natural language legal reports explaining automated signal modifications in 6 languages.
- **Assets**: Quantized binary in [`Model_Vault/`](../Model_Vault/README.md).

---

> 🧭 **Next Chapter**: Discover the ADAGIO™ execution pipeline in [04. Execution Phases & Lifecycle](04_execution_phases.md).

---

<p align="center">
  <sub>SYNAPSE Neural Models — Noxfort Systems</sub><br/>
  <sub><a href="#03-neural-models--pytorch-implementations-markvart">Back to top ↑</a></sub>
</p>
