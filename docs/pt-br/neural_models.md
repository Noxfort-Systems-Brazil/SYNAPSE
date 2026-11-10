# 🧠 SYNAPSE: Stack Neural MARKVART™ e Formulações Matemáticas

Este documento fornece as formulações matemáticas exatas, funções de perda e especificações de operadores PyTorch das 10 redes neurais e motor determinístico que compõem o ecossistema **MARKVART™** (Modular Adaptive Reasoning Kernel with Variational Attention & Recurrent Transformers).

⬅️ [Central de Documentação](README.md) | 🗂️ [Entidades de Domínio](domain_entities.md) | ⏱️ [Fases de Execução](execution_phases.md)

---

## 1. Taxonomia Operacional MARKVART™

Os 10 modelos neurais e o motor de indexação espacial determinístico operam em três camadas sinérgicas:

| Modelo | Subsistema / Agente | Paradigma Matemático | Responsabilidade Primária |
|:---|:---|:---|:---|
| **PINO-Traffic** | Operador Contínuo | Operador Neural de Fourier (FNO) + EDP LWR | Simulação de densidade contínua e ondas de choque. |
| **PI-DeepONet** | Estimador de Campos & Imputador | Rede Dual Branch-Trunk de Operadores | Mapeamento contínuo de campos de velocidade e imputação de lacunas. |
| **iTransformer** | Fusão Multivariada | Atenção com Dimensão Invertida nos Tokens | Fusão espacial entre sensores sem ruído de canais cruzados. |
| **GATv2 Lite / DiffusionGATv2** | Raciocínio em Grafo | Atenção Dinâmica com Tensor Físico 5D (`edge_attr`) + Difusão Harmônica | Propagação espacial ponderada por condutância física e hierarquia viária. |
| **WaveletAE-OCC**| Filtro de Anomalias | Transformada Discreta Wavelet (DWT) + Autoencoder | Detecção de falhas de alta frequência e ataques cibernéticos. |
| **ModernBERT & NeuroSymbolic** | Portão Semântico Zero-Trust | Backbone ModernBERT + TCNAE Desacoplado + Head Físico 3D | Validação semântica e física de esquemas de sensores via perdas LWR. |
| **TCNAE** | Compressão Latente | Convoluções Causais Dilatadas 1D + Portas Residuais| Representação comprimida de séries temporais de sensores. |
| **SpectralFeatureBlock** | Periodicidade Urbana | Convoluções Espectrais de Fourier 1D (`SpectralConv1d`) | Captura padrões diários e semanais de fluxo veicular (substituto otimizado do TimesNet). |
| **FastMapMatcher** | Alinhamento Espacial | Indexação Espacial R-Tree + Distância Fréchet (CPU) | Casamento determinístico sub-microssegundo entre polilinhas multi-segmento Waze/TomTom (`jams`) e eixos viários SUMO. |
| **PI-DVAE-TCN** | Estimativa de Incerteza | Autoencoder Variacional Guiado por Física | Quantificação de incertezas epistêmicas e aleatórias. |
| **Qwen3 Jurist** | Justificador Cognitivo| Small Language Model (SLM) com Isolamento de Processo | Geração de laudos periciais textuais e auditoria sem travar threads de inferência. |

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

## 4. Portão Semântico, Detecção de Anomalias e Explicabilidade Textual

- **ModernBERT & NeuroSymbolicModel (`src/models/modernbert.py`, `src/models/neuro_symbolic.py`)**: Combina o backbone ModernBERT (com aceleração de hardware por Tensor Cores via `allow_tf32 = True`) a um `TCNAE` desacoplado e um Head de Projeção Física 3D $\mathbf{y}_{\text{físico}} = [q, v, \rho]$. Verifica se o fluxo veicular atende às equações de tráfego LWR antes de aprovar dados de sensores em quarentena.
- **WaveletAE-OCC (`src/models/wavelet_ae_occ.py`)**: Decompõe a telemetria bruta de alta frequência usando Wavelets Daubechies ($\psi_{j, k}$) para isolar ruídos espúrios e ataques cibernéticos.
- **Qwen3 Jurist (`src/agents/jurist_agent.py`, `src/slm/`)**: Executado 100% offline via modelos quantizados em GGUF/SafeTensors. Isolado em processo worker dedicado (`src/slm/process/isolated_jurist_manager.py`), garantindo que o processamento do LLM nunca cause atrasos no ciclo de inferência em tempo real (< 250ms) do PyTorch. Gera laudos periciais e derivações matemáticas em conformidade com normas ABNT.

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
