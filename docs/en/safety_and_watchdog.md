# 🛡️ SYNAPSE: Safety, Watchdog & Gating Policy

This document details the neuro-symbolic safety rules, the **F.E.N.I.X.** out-of-process supervisor, health heartbeats, memory limiters, and the multi-tiered **Gating Policy** fallback mechanism.

⬅️ [Documentation Hub](README.md) | 🖥️ [Desktop UI](ui_architecture.md) | 🧪 [Testing & QA](testing.md)

---

## 1. F.E.N.I.X. Out-of-Process Supervisor

To guarantee continuous operation in critical city infrastructures, the cognitive core runs under an independent, out-of-process supervisor (`src/fenix/process_supervisor.py`):

```bash
python synapse.py --supervisor
```

### Core Responsibilities:
1. **Liveness Heartbeats**: The neural core emits heartbeats across an anonymous pipe every 250 ms. If no heartbeat arrives within **500 ms**, the supervisor flags a hang.
2. **Memory Ceiling Enforcement**: The supervisor samples RSS memory. If usage exceeds the configured threshold (e.g., 4096 MB), it commands an orderly garbage collection or initiates a clean process rollover.
3. **Autonomous Resurrection**: In the event of a segfault, CUDA out-of-memory error, or unhandled exception, F.E.N.I.X. spawns a replacement worker within **< 1.0 s**, restoring state from the latest validated checkpoint.

---

## 2. Multi-Tiered Gating Policy

When sensory data degrades or drops out, the system cannot feed nulls or NaNs into the neural pipeline. The **Gating Policy** (`src/domain/gating_policy.py`) executes a graceful degradation cascade:

```
┌────────────────────────────────────────────────────────┐
│                   GATING POLICY CASCADE                │
│                                                        │
│  [Tier 1: Neural Perception]                           │
│  Full MARKVART™ inference on validated active sensors  │
│                           │                            │
│                           ▼ (Packet drop detected)     │
│  [Tier 2: Kinematic Dead Reckoning (KSE)]              │
│  Kalman filter kinematic extrapolation (v, a)          │
│                           │                            │
│                           ▼ (> 30s communication loss) │
│  [Tier 3: Historical Micro-Estimation (MEH)]           │
│  Calibrated historical baseline profiles               │
└────────────────────────────────────────────────────────┘
```

- **Tier 1 (Neural)**: Standard operation with trust score $\tau \ge 0.70$.
- **Tier 2 (KSE)**: Activates upon instantaneous packet loss ($1 \le N_{\text{missed}} \le 30$). Maintains fluid dynamics consistency without artificial jumps.
- **Tier 3 (Historical)**: Activates under sustained hardware failure. Injects baseline time-of-day traffic distributions until the field unit is restored.

---

## 3. Symbolic Validation Rules

Before telemetry enters the tensor pipeline, it must pass deterministic invariant checks:
- **`SR-01 (Speed Ceiling)`**: $v \le 180\text{ km/h}$ on urban roads.
- **`SR-02 (Acceleration Invariant)`**: $|a| \le 8.5\text{ m/s}^2$ (physical braking/acceleration limits).
- **`SR-03 (Density Ceiling)`**: $\rho \le \rho_{\text{jam}} = 140\text{ veh/km/lane}$.
- **`SR-04 (Flow Conservation)`**: Node inflow/outflow balance within physical bounds.

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
