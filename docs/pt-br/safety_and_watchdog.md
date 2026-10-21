# 🛡️ SYNAPSE: Segurança, Watchdog e Política de Degradação

Este documento detalha as regras neuro-simbólicas de segurança, o supervisor independente **F.E.N.I.X.**, o monitoramento de batimentos cardíacos (heartbeats), tetos de memória e a política de degradação em cascata (**Gating Policy**).

⬅️ [Central de Documentação](README.md) | 🖥️ [Interface Desktop](ui_architecture.md) | 🧪 [Testes e QA](testing.md)

---

## 1. Supervisor Independente F.E.N.I.X.

Para assegurar disponibilidade ininterrupta, o núcleo neural do SYNAPSE opera sob o supervisor out-of-process (`src/fenix/process_supervisor.py`):

```bash
python synapse.py --supervisor
```

### Atribuições Críticas:
1. **Batimentos Cardíacos (Heartbeats)**: O núcleo neural emite pulsos por pipe anônimo a cada 250 ms. Se nenhum pulso for detectado em **500 ms**, o supervisor sinaliza travamento.
2. **Controle de Teto de Memória**: O supervisor monitora o uso de RSS. Se o limite configurado (ex: 4096 MB) for violado, comanda coleta de lixo forçada ou reinicialização controlada de processo.
3. **Ressurreição Autônoma**: Caso ocorra falha de segmentação, estouro de memória CUDA ou exceção não tratada, o F.E.N.I.X. instancia um novo worker em **menos de 1,0 s**, restaurando o último estado validado.

---

## 2. Política de Degradação Suave (Gating Policy)

Em caso de degradação severa ou ausência de dados, a **Gating Policy** (`src/domain/gating_policy.py`) impede a propagação de valores nulos nos tensores neurais:

```
┌────────────────────────────────────────────────────────┐
│               CASCATA DA GATING POLICY                 │
│                                                        │
│  [Nível 1: Percepção Neural Plena]                     │
│  Inferência completa MARKVART™ com sensores ativos     │
│                           │                            │
│                           ▼ (Perda transitória)        │
│  [Nível 2: Dead Reckoning Cinemático (KSE)]            │
│  Extrapolação via Filtro de Kalman (v, a)              │
│                           │                            │
│                           ▼ (> 30s de indisponibilidade│
│  [Nível 3: Micro-Estimação Histórica (MEH)]            │
│  Perfis estatísticos calibrados por dia e horário      │
└────────────────────────────────────────────────────────┘
```

- **Nível 1 (Neural)**: Operação normal com score de confiança $\tau \ge 0,70$.
- **Nível 2 (KSE)**: Ativado na perda momentânea de pacotes ($1 \le N_{\text{missed}} \le 30$). Mantém fluidez contínua sem descontinuidades abruptas.
- **Nível 3 (Histórico)**: Ativado em caso de pane física prolongada no sensor, injetando médias históricas até o reparo do equipamento.

---

## 3. Regras de Invariantes Físicos

Todos os pacotes são submetidos a validações determinísticas antes do pipeline:
- **`SR-01 (Teto de Velocidade)`**: $v \le 180\text{ km/h}$ em vias urbanas.
- **`SR-02 (Invariante de Aceleração)`**: $|a| \le 8,5\text{ m/s}^2$ (limite físico de frenagem/aceleração).
- **`SR-03 (Densidade Crítica)`**: $\rho \le \rho_{\text{jam}} = 140\text{ veíc/km/faixa}$.
- **`SR-04 (Conservação de Fluxo)`**: Balanço volumétrico coerente entre nós contíguos.

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
