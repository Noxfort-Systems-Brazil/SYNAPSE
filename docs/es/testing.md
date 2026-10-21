# 🧪 SYNAPSE: Pruebas y Aseguramiento de Calidad

Este documento define la infraestructura de pruebas automatizadas, las suites Pytest, generadores de telemetría sintética y criterios de cobertura de código en **SYNAPSE CORE**.

⬅️ [Centro de Documentación](README.md) | 🛡️ [Seguridad y Watchdog](safety_and_watchdog.md) | 🏛️ [Arquitectura Central](architecture.md)

---

## 1. Organización de las Suites de Pruebas

El repertorio de pruebas se localiza en `tests/` y comprende:

- **Pruebas Unitarias (`tests/unit/`)**: Comprobación individual de entidades de dominio y transiciones de estados.
- **Pruebas de Redes Neuronales (`tests/models/`)**: Verificación de pasadas forward/backward, dimensiones tensoriales y estabilidad de gradientes en los 11 modelos MARKVART™.
- **Pruebas de Integración (`tests/integration/`)**: Validación integral desde adaptadores de entrada hasta la salida gRPC.
- **Pruebas de IPC (`tests/ipc/`)**: Verificación del protocolo JSON-RPC Stdio contra ráfagas de datos y mensajes truncados.
- **Benchmarks (`tests/benchmarks/`)**: Medición de latencia de ciclo de inferencia y tasa de serialización.

---

## 2. Ejecución de Pruebas

Active el entorno virtual antes de ejecutar:

```bash
source .venv/bin/activate
```

### Ejecutar Suite Completa Pytest:
```bash
pytest tests/ -v
```

### Ejecutar con Reporte de Cobertura:
```bash
pytest --cov=src --cov-report=term-missing --cov-report=html tests/
```

### Ejecutar Únicamente Modelos Neuronales:
```bash
pytest tests/test_neural_models.py -v
```

---

## 3. Datos Sintéticos y Mocks Deterministas

Para viabilizar pruebas en entornos cerrados sin hardware de campo:

- **`SyntheticTrafficGenerator`**: Simula dinámicas de vehículos apoyándose en el modelo de Greenshields.
- **`MockHftReceiver`**: Receptor gRPC simulado en memoria para corroborar latencia y conformidad con el esquema.
- **Semillas Deterministas**: Fijación de semillas aleatorias (`torch.manual_seed(42)`) para garantizar total repetibilidad.

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
