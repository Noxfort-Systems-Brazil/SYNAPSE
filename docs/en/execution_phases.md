# ⏱️ SYNAPSE: ADAGIO™ Execution Phases & KSE Kinematics

This document describes the structured runtime lifecycle of the **ADAGIO™** (Adaptive Distributed Autonomous Graph Ingestion & Optimization) engine and the **Kinematic State Estimation (KSE)** dead reckoning module.

⬅️ [Documentation Hub](README.md) | 🧠 [MARKVART™ Neural Stack](neural_models.md) | ⚡ [Data Ingestion & HFT](data_ingestion_and_hft.md)

---

## 1. ADAGIO™ Phase Progression

SYNAPSE manages operational execution across three strictly defined phases:

```
┌────────────────────────────────┐
│   Phase 0: AutoML Tuning       │  ◄── Optuna Bayesian Optimization of hyperparameters
└───────────────┬────────────────┘
                │ Best parameters converged
┌───────────────▼────────────────┐
│   Phase 1: Golden Bootstrap    │  ◄── Ingests historical parquet logs & calibrates baselines
└───────────────┬────────────────┘
                │ Ghost-file verified & SafeTensors compiled
┌───────────────▼────────────────┐
│   Phase 2: Online Concurrency  │  ◄── High-frequency 4-thread real-time runtime loop
└────────────────────────────────┘
```

### Phase 0: AutoML Optimization
- Executes automated Bayesian optimization over model hyperparameters using **Optuna**.
- Explores learning rates, FNO spectral modes ($k_{\max} \in [8, 32]$), GATv2 attention heads ($h \in [2, 8]$), and temporal patch lengths.
- Employs pruning algorithms (MedianPruner) to abort non-convergent configurations early.

### Phase 1: Golden Dataset Bootstrap
- Ingests raw historical municipal records, OpenStreetMap geometries, and loop sensor archives.
- Produces normalized, sanitized, and physically validated tensors (**Golden Dataset**).
- **Ghost-File Protection**: Writes atomically to `.tmp` files and executes SHA-256 integrity checks before moving into the production cache, guaranteeing zero corruption during sudden shutdowns.

### Phase 2: Online 4-Thread Concurrency Runtime
The operational runtime orchestrates four dedicated, non-blocking asynchronous threads:

1. **Ingestion Thread**: Listens on HTTP/MQTT/WebSocket adapters, decodes sensor payloads, and verifies Bayesian trust scores.
2. **Kinematic / Dead Reckoning Thread (KSE)**: Computes position and velocity updates via Kalman filtering for sensors experiencing packet drop.
3. **Neural Inference Thread**: Executes the MARKVART™ forward passes via PyTorch CUDA streams (PINO, GATv2, iTransformer).
4. **HFT Streaming Thread**: Bundles macroscopic density matrices into Protobuf messages and pushes them across the gRPC stream.

---

## 2. Kinematic State Estimation (KSE) Dead Reckoning & Hydrodynamics

When a field sensor encounters network packet drops, signal loss, or slower polling cadences, the system activates **KSE Kinematic Dead Reckoning** and **Macroscopic Hydrodynamics** to maintain uninterrupted physical continuity:

### Discrete Kalman Filter (UKF) State Vector
$$\mathbf{x}_k = \begin{bmatrix} s_k \\ v_k \\ a_k \end{bmatrix}$$

Where $s_k$ is segment displacement, $v_k$ is velocity, and $a_k$ is acceleration.

### State Transition Model & Internal Synchronization:
$$\mathbf{x}_{k+1} = \mathbf{F} \mathbf{x}_k + \mathbf{w}_k, \quad \mathbf{F} = \begin{bmatrix} 1 & \Delta t & \frac{1}{2}\Delta t^2 \\ 0 & 1 & \Delta t \\ 0 & 0 & 1 \end{bmatrix}, \quad \mathbf{w}_k \sim \mathcal{N}(0, \mathbf{Q})$$

- **UKF Internal State Synchronization (`KSEInertialImputationStrategy`)**: Immediately after clamping and decaying `ghost_step()` projections, the internal UKF state `physics_engine.x[0, 0]` is synchronized with `new_val` and divergent accelerations are zeroed, preventing exponential drift toward zero.
- **Global Polling Observability Window (`SnapshotBuilder`)**: Preserves active spatial observation masks (`M_t = 1.0`) for up to `fallback_steps <= 75` ($\sim 60\text{s}$), matching the natural polling cadence of external global APIs (Waze/TomTom) while applying gradual confidence decay ($0.985^{\text{steps}}$).
- **Road-Hierarchy Hydrodynamic Interpolation (`TrafficHydrodynamicEngine`)**: Weights node speeds and densities by road hierarchy permeability (`perm` $\in [0.15, 1.15]$ from `edge_type`, `priority`, and `lanes`) and segment geometry (`geom_factor`), prioritizing direct inductive loop readings or matched Waze jams.
- **Physical Queue Estimation (`TrafficQueueCalculator`)**: Computes `estimated_queue_m` from real-time speed reduction ($v_{\text{ratio}} = v_{\text{edge}} / v_{\max} < 0.85$) and shockwave density saturation ($\rho > 18.0\text{ veh/km}$).

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
