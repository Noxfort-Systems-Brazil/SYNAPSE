# 🧠 SYNAPSE: Stack Neural MARKVART™ y Formulaciones Matemáticas

Este documento expone las formulaciones matemáticas rigurosas, funciones de pérdida y especificaciones de operadores PyTorch de las 10 redes neuronales y motor determinista que integran el ecosistema **MARKVART™** (Modular Adaptive Reasoning Kernel with Variational Attention & Recurrent Transformers).

⬅️ [Centro de Documentación](README.md) | 🗂️ [Entidades de Dominio](domain_entities.md) | ⏱️ [Fases de Ejecución](execution_phases.md)

---

## 1. Taxonomía Funcional MARKVART™

Las 10 arquitecturas neuronales y el motor de alineación espacial determinista operan coordinadas en tres niveles:

| Modelo | Subsistema / Agente | Paradigma Matemático | Responsabilidad Primaria |
|:---|:---|:---|:---|
| **PINO-Traffic** | Operador Continuo | Operador Neural de Fourier (FNO) + EDP LWR | Simulación continua de densidad vehicular y ondas de choque. |
| **PI-DeepONet** | Estimador de Campos | Red Dual Branch-Trunk de Operadores | Mapeo no lineal en dimensión infinita para campos de velocidad. |
| **iTransformer** | Fusión Multivariada | Atención con Dimensión Invertida en Tokens | Fusión espacial de sensores sin distorsión entre canales. |
| **GATv2 Lite** | Razonamiento en Grafo | Atención Dinámica Espaciotemporal en Grafos | Propagación de congestión vehicular entre cruces vecinos. |
| **WaveletAE-OCC**| Detección de Anomalías | Transformada Wavelet Discreta (DWT) + Autoencoder | Detección de perturbaciones de alta frecuencia e intrusiones. |
| **PatchTST** | Pronóstico por Parches | Patching Temporal + Atención Independiente | Proyección multietapa de velocidad y ocupación de calzada. |
| **TCNAE** | Compresión Latente | Convoluciones Causales Dilatadas 1D + Compuertas | Representación comprimida de series temporales de sensores. |
| **TimesNet** | Periodicidad Urbana | Transformada Fourier 2D + Módulos Inception | Captura periodicidad diurna y semanal del flujo de tráfico. |
| **FastMapMatcher** | Alineación Espacial | Indexación Espacial R-Tree + Distancia Fréchet (CPU) | Resolución determinista sub-microsegundo de discrepancias espaciales entre polilíneas externas y red vial SUMO. |
| **PI-DVAE-TCN** | Estimación de Incertidumbre | Autoencoder Variacional Guiado por Física | Cuantificación de incertidumbre epistémica y aleatoria. |
| **Qwen3 Jurist** | Justificador Cognitivo| Modelo de Lenguaje Pequeño (SLM) en GGUF 4-bit | Redacción de explicaciones textuales y justificaciones periciales. |

---

## 2. Operadores Neuronales Informados por la Física

### PINO-Traffic (Physics-Informed Neural Operator)
- **Módulo**: `src/models/pino_traffic.py`
- **Ecuación Rectora**: Ecuación Diferencial Parcial de Conservación de Lighthill-Whitham-Richards (LWR):

$$\frac{\partial \rho}{\partial t} + \frac{\partial (\rho \cdot v)}{\partial x} = 0, \quad v(\rho) = v_f \left(1 - \frac{\rho}{\rho_{\text{jam}}}\right)$$

#### Función de Pérdida Residual Física:
$$\mathcal{L}_{\text{PINO}} = \mathcal{L}_{\text{datos}} + \lambda_{\text{pde}} \mathcal{L}_{\text{pde}} + \lambda_{\text{ic}} \mathcal{L}_{\text{ic}}$$

$$\mathcal{L}_{\text{pde}} = \left\| \frac{\partial \rho_{\theta}}{\partial t} + \frac{\partial}{\partial x}\left(\rho_{\theta} \cdot v(\rho_{\theta})\right) \right\|_{L^2}^2$$

### PI-DeepONet (Aproximador Continuo de Operadores)
- **Módulo**: `src/models/pi_deeponet.py`
- Modela condiciones de borde mediante una red **Branch** $b(u)$ y coordenadas de consulta mediante una red **Trunk** $t(y)$:

$$G_{\theta}(u)(y) \approx \sum_{k=1}^P b_k(u) \cdot t_k(y) + b_0$$

---

## 3. Fusión Espaciotemporal de Alto Rendimiento

### iTransformer (Atención Invertida)
- **Módulo**: `src/models/itransformer.py`
Proyecta la serie temporal de cada sensor como un token individual:

$$\mathbf{H}_i = \text{Embedding}(\mathbf{X}_{:, i}) \in \mathbb{R}^D$$

$$\mathbf{Z} = \text{Softmax}\left(\frac{\mathbf{Q}\mathbf{K}^T}{\sqrt{D}}\right)\mathbf{V}$$

### GATv2 Lite (Atención Dinámica en Grafos)
- **Módulo**: `src/models/gatv2_lite.py`
Ajusta dinámicamente los pesos de atención entre aristas conectadas:

$$\alpha_{ij} = \frac{\exp\left(\mathbf{a}^T \text{LeakyReLU}\left(\mathbf{W}_1 \mathbf{h}_i + \mathbf{W}_2 \mathbf{h}_j\right)\right)}{\sum_{k \in \mathcal{N}(i)} \exp\left(\mathbf{a}^T \text{LeakyReLU}\left(\mathbf{W}_1 \mathbf{h}_i + \mathbf{W}_2 \mathbf{h}_k\right)\right)}$$

---

## 4. Justificación Textual con Qwen3 Jurist

El modelo **Qwen3 Jurist** corre en modo puramente local mediante llama.cpp (GGUF 4-bit), formulando dictámenes periciales en lenguaje natural ante anomalías o solicitudes de onda verde prioritaria.

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
