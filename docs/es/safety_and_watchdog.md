# 🛡️ SYNAPSE: Seguridad, Watchdog y Política de Degradación

Este documento detalla el marco neuro-simbólico de seguridad, el supervisor independiente **F.E.N.I.X.**, el control de señales de vida (heartbeats), límites de memoria y la política escalonada de degradación (**Gating Policy**).

⬅️ [Centro de Documentación](README.md) | 🖥️ [Interfaz de Escritorio](ui_architecture.md) | 🧪 [Pruebas y QA](testing.md)

---

## 1. Supervisor Independiente F.E.N.I.X.

Para asegurar disponibilidad de misión crítica, el núcleo neural corre bajo un supervisor out-of-process (`src/fenix/process_supervisor.py`):

```bash
python synapse.py --supervisor
```

### Funciones Primordiales:
1. **Señales de Vida (Heartbeats)**: El núcleo emite señales por un canal anónimo cada 250 ms. La ausencia de señales durante **500 ms** detona una alerta de bloqueo.
2. **Control de Memoria RAM**: Monitorea el consumo RSS. Si supera el umbral fijado (ej. 4096 MB), fuerza recolección de basura o reinicio ordenado de worker.
3. **Resurrección Automática**: Ante errores de segmentación o desbordamiento de memoria CUDA, F.E.N.I.X. genera un nuevo proceso en **menos de 1.0 s**, restableciendo el último estado consolidado.

---

## 2. Política de Degradación Escalonada (Gating Policy)

Ante interrupciones en la recepción de datos, la **Gating Policy** (`src/domain/gating_policy.py`) previene la inyección de valores nulos:

```
┌────────────────────────────────────────────────────────┐
│             CASCADA DE GATING POLICY                   │
│                                                        │
│  [Nivel 1: Percepción Neural Completa]                 │
│  Inferencia MARKVART™ sobre sensores activos           │
│                           │                            │
│                           ▼ (Caída de paquetes)        │
│  [Nivel 2: Dead Reckoning Cinemático (KSE)]            │
│  Extrapolación con Filtro de Kalman (v, a)             │
│                           │                            │
│                           ▼ (> 30s de corte sostenido) │
│  [Nivel 3: Micro-Estimación Histórica (MEH)]           │
│  Líneas base históricas calibradas por franja horaria  │
└────────────────────────────────────────────────────────┘
```

- **Nivel 1 (Neural)**: Régimen regular con índice de confianza $\tau \ge 0.70$.
- **Nivel 2 (KSE)**: Activación ante pérdidas transitorias ($1 \le N_{\text{missed}} \le 30$).
- **Nivel 3 (Histórico)**: Activación ante averías prolongadas en sensores de campo.

---

## 3. Reglas de Invariantes Físicos

Todos los paquetes atraviesan filtros deterministas antes de ingresar al pipeline:
- **`SR-01 (Límite de Velocidad)`**: $v \le 180\text{ km/h}$ en vías urbanas.
- **`SR-02 (Invariante de Aceleración)`**: $|a| \le 8.5\text{ m/s}^2$ (límites dinámicos de frenado).
- **`SR-03 (Densidad Crítica)`**: $\rho \le \rho_{\text{jam}} = 140\text{ veh/km/carril}$.
- **`SR-04 (Conservación de Flujo)`**: Coherencia en balances de entrada y salida nodal.

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
