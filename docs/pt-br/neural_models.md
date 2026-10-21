# 🧠 SYNAPSE: Stack Neural MARKVART™ e Formulações Matemáticas

Este documento fornece as formulações matemáticas exatas, funções de perda e especificações de operadores PyTorch das 10 redes neurais e motor determinístico que compõem o ecossistema **MARKVART™** (Modular Adaptive Reasoning Kernel with Variational Attention & Recurrent Transformers).

⬅️ [Central de Documentação](README.md) | 🗂️ [Entidades de Domínio](domain_entities.md) | ⏱️ [Fases de Execução](execution_phases.md)

---

## 1. Taxonomia Operacional MARKVART™

Os 10 modelos neurais e o motor de indexação espacial determinístico operam em três camadas sinérgicas:

| Modelo | Subsistema / Agente | Paradigma Matemático | Responsabilidade Primária |
|:---|:---|:---|:---|
| **PINO-Traffic** | Operador Contínuo | Operador Neural de Fourier (FNO) + EDP LWR | Simulação de densidade contínua e ondas de choque. |
| **PI-DeepONet** | Estimador de Campos | Rede Dual Branch-Trunk de Operadores | Mapeamento não-linear de campos de velocidade. |
| **iTransformer** | Fusão Multivariada | Atenção com Dimensão Invertida nos Tokens | Fusão espacial entre sensores sem ruído de canais cruzados. |
| **GATv2 Lite / DiffusionGATv2** | Raciocínio em Grafo | Atenção Dinâmica com Tensor Físico 5D (`edge_attr`) + Difusão Harmônica | Propagação espacial ponderada por condutância física e hierarquia viária. |
| **WaveletAE-OCC**| Filtro de Anomalias | Transformada Discreta Wavelet (DWT) + Autoencoder | Detecção de falhas de alta frequência e ataques cibernéticos. |
| **PatchTST** | Previsão por Blocos | Patching Temporal + Atenção Independente por Canal | Projeção multi-etapas de velocidades e ocupações de via. |
| **TCNAE** | Compressão Latente | Convoluções Causais Dilatadas 1D + Portas Residuais| Representação comprimida de séries temporais de sensores. |
| **TimesNet** | Periodicidade Urbana | Decomposição 2D por Fourier + Blocos Inception | Captura padrões diários e semanais de fluxo veicular. |
| **FastMapMatcher** | Alinhamento Espacial | Indexação Espacial R-Tree + Distância Fréchet (CPU) | Casamento determinístico sub-microssegundo entre polilinhas multi-segmento Waze/TomTom (`jams`) e eixos viários SUMO. |
| **PI-DVAE-TCN** | Estimativa de Incerteza | Autoencoder Variacional Guiado por Física | Quantificação de incertezas epistêmicas e aleatórias. |
| **Qwen3 Jurist** | Justificador Cognitivo| Small Language Model (SLM) quantizado em GGUF | Geração de laudos periciais textuais e justificativas. |

---

## 2. Operadores Neurais Informados pela Física

### PINO-Traffic (Physics-Informed Neural Operator)
- **Módulo**: `src/models/pino_traffic.py`
- **Equação Governante**: Equação Diferencial Parcial de Conservação de Lighthill-Whitham-Richards (LWR):

$$\frac{\partial \rho}{\partial t} + \frac{\partial (\rho \cdot v)}{\partial x} = 0, \quad v(\rho) = v_f \left(1 - \frac{\rho}{\rho_{\text{jam}}}\right)$$

#### Função de Perda Física Residual:
$$\mathcal{L}_{\text{PINO}} = \mathcal{L}_{\text{dados}} + \lambda_{\text{pde}} \mathcal{L}_{\text{pde}} + \lambda_{\text{ic}} \mathcal{L}_{\text{ic}}$$

$$\mathcal{L}_{\text{pde}} = \left\| \frac{\partial \rho_{\theta}}{\partial t} + \frac{\partial}{\partial x}\left(\rho_{\theta} \cdot v(\rho_{\theta})\right) \right\|_{L^2}^2$$

### PI-DeepONet (Aproximador Contínuo de Campos)
- **Módulo**: `src/models/pi_deeponet.py`
- Mapeia condições de contorno via **Branch Network** $b(u)$ e coordenadas espaço-temporais via **Trunk Network** $t(y)$:

$$G_{\theta}(u)(y) \approx \sum_{k=1}^P b_k(u) \cdot t_k(y) + b_0$$

---

## 3. Fusão Espacial e Temporal Avançada

### iTransformer (Atenção Invertida)
- **Módulo**: `src/models/itransformer.py`
Ao contrário dos Transformers convencionais, o **iTransformer** projeta a série temporal inteira de cada sensor como um token individual no espaço de atenção:

$$\mathbf{H}_i = \text{Embedding}(\mathbf{X}_{:, i}) \in \mathbb{R}^D$$

$$\mathbf{Z} = \text{Softmax}\left(\frac{\mathbf{Q}\mathbf{K}^T}{\sqrt{D}}\right)\mathbf{V}$$

Garantindo que a correlação espacial entre vias distintas seja computada por auto-atenção sem contaminação entre canais.

### GATv2 Lite & DiffusionGATv2 (Atenção e Difusão Física em Grafo)
- **Módulos**: `src/models/gatv2_lite.py`, `src/models/diffusion_gatv2.py`
Atualiza dinamicamente os coeficientes de atenção entre nós conectados da malha viária incorporando o vetor físico 5D da aresta ($\mathbf{e}_{ij} \in \mathbb{R}^{E \times 5}$: comprimento normalizado, velocidade máxima, número de faixas, prioridade/hierarquia viária e condutância física):

$$\alpha_{ij} = \frac{\exp\left(\mathbf{a}^T \text{LeakyReLU}\left(\mathbf{W}_1 \mathbf{h}_i + \mathbf{W}_2 \mathbf{h}_j + \mathbf{W}_e \mathbf{e}_{ij}\right)\right)}{\sum_{k \in \mathcal{N}(i)} \exp\left(\mathbf{a}^T \text{LeakyReLU}\left(\mathbf{W}_1 \mathbf{h}_i + \mathbf{W}_2 \mathbf{h}_k + \mathbf{W}_e \mathbf{e}_{ik}\right)\right)}$$

No `FusionPipeline`, nós não observados ($M_i = 0$) são reconstruídos combinando a projeção neural do `DiffusionGATv2` com uma **difusão harmônica amortecida de 8 saltos (8-hop)** ponderada pela condutância física e ancorada num prior topológico (`y_bg`), preservando gradientes espaciais realistas em toda a malha.

---

## 4. Auditoria Pericial Textual com Qwen3 Jurist

O modelo **Qwen3 Jurist** é executado 100% offline via llama.cpp em precisão quantizada GGUF (4 bits), gerando parágrafos periciais em conformidade com normas forenses que justificam anomalias ou acionamentos de sinalização prioritária.

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
