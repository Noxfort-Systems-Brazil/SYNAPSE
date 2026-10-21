# ⏱️ SYNAPSE: Fases de Ejecución ADAGIO™ y Cinemática KSE

Este documento describe el ciclo de vida estructurado del motor **ADAGIO™** (Adaptive Distributed Autonomous Graph Ingestion & Optimization) y el módulo de estimación cinemática por Dead Reckoning **KSE** (Kinematic State Estimation).

⬅️ [Centro de Documentación](README.md) | 🧠 [Stack Neural MARKVART™](neural_models.md) | ⚡ [Ingestión y HFT](data_ingestion_and_hft.md)

---

## 1. Progresión de Fases ADAGIO™

SYNAPSE organiza su ciclo operativo a través de tres fases estrictas:

```
┌────────────────────────────────┐
│   Fase 0: Optimización AutoML  │  ◄── Búsqueda Bayesiana con Optuna
└───────────────┬────────────────┘
                │ Convergencia de parámetros óptimos
┌───────────────▼────────────────┐
│   Fase 1: Bootstrap Dorado     │  ◄── Ingesta de registros históricos y calibración
└───────────────┬────────────────┘
                │ Verificación de integridad Ghost-File
┌───────────────▼────────────────┐
│   Fase 2: Concurrencia Online  │  ◄── Bucle de tiempo real con 4 hilos dedicados
└────────────────────────────────┘
```

### Fase 0: Optimización AutoML
- Ejecuta búsqueda bayesiana de hiperparámetros con **Optuna**: tasas de aprendizaje, modos espectrales FNO ($k_{\max} \in [8, 32]$) y cabezas de atención GATv2.
- Aplica mecanismos de poda estadística (`MedianPruner`) para interrumpir pruebas no prometedoras.

### Fase 1: Bootstrap del Golden Dataset
- Carga registros históricos municipales, geometrías viales de OpenStreetMap y series de sensores.
- Genera tensores normalizados y matemáticamente validados (**Dataset Dorado**).
- **Protección Ghost-File**: Escritura atómica en archivos temporales con validación SHA-256 antes de consolidar el cache de producción.

### Fase 2: Runtime con 4 Hilos Concurrentes
El entorno de ejecución en tiempo real orquesta cuatro hilos no bloqueantes:

1. **Hilo de Ingestión**: Recibe paquetes de adaptadores HTTP/MQTT/WebSocket y evalúa puntajes Bayesianos.
2. **Hilo Cinemático (KSE)**: Calcula proyecciones continuas mediante Filtros de Kalman ante pérdida de paquetes.
3. **Hilo de Inferencia Neural**: Ejecuta modelos MARKVART™ en GPU mediante CUDA Streams (PINO, GATv2, iTransformer).
4. **Hilo de Streaming HFT**: Empaqueta matrices de densidad en formato Protobuf y transmite vía gRPC hacia CARINA.

---

## 2. Estimación Cinemática (KSE) Dead Reckoning

Ante caídas intermitentes de red en los sensores de campo, el módulo **KSE Dead Reckoning** garantiza la continuidad del flujo:

### Vector de Estado en el Filtro de Kalman Discreto
$$\mathbf{x}_k = \begin{bmatrix} s_k \\ v_k \\ a_k \end{bmatrix}$$

Donde $s_k$ representa desplazamiento, $v_k$ velocidad y $a_k$ aceleración.

### Ecuación de Transición de Estados:
$$\mathbf{x}_{k+1} = \mathbf{F} \mathbf{x}_k + \mathbf{w}_k$$

$$\mathbf{F} = \begin{bmatrix} 1 & \Delta t & \frac{1}{2}\Delta t^2 \\ 0 & 1 & \Delta t \\ 0 & 0 & 1 \end{bmatrix}, \quad \mathbf{w}_k \sim \mathcal{N}(0, \mathbf{Q})$$

Si un sensor no emite datos durante $N_{\text{missed}} \ge 3$ ciclos consecutivos, el estado cinemático estimado sustituye la lectura directa y degrada la fuente a `FALLBACK`.

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
