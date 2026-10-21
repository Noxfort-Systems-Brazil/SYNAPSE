# ⏱️ SYNAPSE: Fases de Execução ADAGIO™ e Cinemática KSE

Este documento detalha o ciclo de vida estruturado do motor **ADAGIO™** (Adaptive Distributed Autonomous Graph Ingestion & Optimization) e o módulo de estimativa por Dead Reckoning **KSE** (Kinematic State Estimation).

⬅️ [Central de Documentação](README.md) | 🧠 [Stack Neural MARKVART™](neural_models.md) | ⚡ [Ingestão e HFT](data_ingestion_and_hft.md)

---

## 1. Progressão das Fases ADAGIO™

O SYNAPSE estrutura sua execução operacional em três fases rigorosas:

```
┌────────────────────────────────┐
│   Fase 0: Otimização AutoML    │  ◄── Otimização Bayesiana de hiperparâmetros via Optuna
└───────────────┬────────────────┘
                │ Convergência dos parâmetros ótimos
┌───────────────▼────────────────┐
│   Fase 1: Bootstrap Dourado    │  ◄── Ingestão de arquivos históricos e calibração de base
└───────────────┬────────────────┘
                │ Verificação anti-corrupção Ghost-File
┌───────────────▼────────────────┐
│   Fase 2: Concorrência Online  │  ◄── Loop de tempo real com 4 threads dedicadas
└────────────────────────────────┘
```

### Fase 0: Otimização AutoML (Optuna)
- Realiza busca bayesiana nos hiperparâmetros das redes MARKVART™: taxa de aprendizado, modos espectrais no FNO ($k_{\max} \in [8, 32]$) e cabeças de atenção no GATv2.
- Utiliza podadores estatísticos (`MedianPruner`) para abortar configurações sub-ótimas precocemente.

### Fase 1: Bootstrap do Dataset Dourado (Golden Dataset)
- Carrega registros históricos municipais, malha viária do OpenStreetMap e dados de laços indutivos.
- Gera tensores normalizados e matematicamente consistentes (**Dataset Dourado**).
- **Proteção Ghost-File**: Escrita atômica em arquivos temporários com validação SHA-256 antes da gravação final, eliminando risco de tensores corrompidos.

### Fase 2: Runtime com 4 Threads Concorrentes
O ambiente operacional de tempo real executa quatro threads não-bloqueantes:

1. **Thread de Ingestão**: Coleta dados via adaptadores HTTP/MQTT/WebSocket e valida trust scores.
2. **Thread Cinemática (KSE)**: Calcula estimativas de posição e velocidade via Filtro de Kalman em trechos com falha de transmissão.
3. **Thread de Inferência Neural**: Executa os modelos MARKVART™ em GPU via CUDA Streams (PINO, GATv2, iTransformer).
4. **Thread de Streaming HFT**: Serializa as matrizes de densidade em Protobuf e transmite via gRPC para os controladores semafóricos.

---

## 2. Dead Reckoning Cinemático (KSE) e Hidrodinâmica Viária

Em caso de interrupção transitória de pacotes ou diferenças de cadência entre sensores locais e APIs globais, o módulo **KSE Dead Reckoning** e o motor hidrodinâmico asseguram continuidade física:

### Vetor de Estado no Filtro de Kalman (UKF)
$$\mathbf{x}_k = \begin{bmatrix} s_k \\ v_k \\ a_k \end{bmatrix}$$

Onde $s_k$ é o deslocamento no segmento, $v_k$ a velocidade e $a_k$ a aceleração.

### Modelo de Transição e Sincronização Interna:
$$\mathbf{x}_{k+1} = \mathbf{F} \mathbf{x}_k + \mathbf{w}_k, \quad \mathbf{F} = \begin{bmatrix} 1 & \Delta t & \frac{1}{2}\Delta t^2 \\ 0 & 1 & \Delta t \\ 0 & 0 & 1 \end{bmatrix}, \quad \mathbf{w}_k \sim \mathcal{N}(0, \mathbf{Q})$$

- **Sincronização do Estado Interno UKF (`KSEInertialImputationStrategy`)**: Após aplicar limites físicos e decaimento em `ghost_step()`, o estado interno `physics_engine.x[0, 0]` é sincronizado com o valor limitado (`new_val`) e acelerações divergentes são zeradas, evitando deriva exponencial para zero.
- **Janela de Observabilidade Global (`SnapshotBuilder`)**: Mantém a máscara de observação ativa (`M_t = 1.0`) por até `fallback_steps <= 75` ($\sim 60\text{s}$), cobrindo o intervalo natural de polling de APIs globais (Waze/TomTom) com decaimento gradual de confiança ($0.985^{\text{steps}}$).
- **Interpolação Hidrodinâmica por Hierarquia Viária (`TrafficHydrodynamicEngine`)**: Pondera velocidades e densidades pelas propriedades físicas da via (`edge_type`, `priority`, `lanes`, fator geométrico `geom_factor` e permeabilidade `perm` $\in [0.15, 1.15]$), priorizando leituras reais de laços indutivos ou congestionamentos mapeados.
- **Cálculo Físico de Fila (`TrafficQueueCalculator`)**: Estima `estimated_queue_m` combinando razão de redução de velocidade ($v_{\text{ratio}} = v_{\text{edge}} / v_{\max} < 0.85$) e saturação de densidade de onda de choque ($\rho > 18.0\text{ veh/km}$).

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
