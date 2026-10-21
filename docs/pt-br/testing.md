# 🧪 SYNAPSE: Diretrizes de Testes e Garantia de Qualidade

Este documento apresenta a infraestrutura de testes automatizados, suítes Pytest, geradores de telemetria sintética e critérios de cobertura de código do **SYNAPSE CORE**.

⬅️ [Central de Documentação](README.md) | 🛡️ [Segurança e Watchdog](safety_and_watchdog.md) | 🏛️ [Arquitetura Central](architecture.md)

---

## 1. Organização das Suítes de Testes

A suíte de testes reside no diretório `tests/` e divide-se em:

- **Testes Unitários (`tests/unit/`)**: Verificação isolada de entidades de domínio, cálculos cinemáticos e máquinas de estado.
- **Testes de Modelos Neurais (`tests/models/`)**: Checagem de passadas direta/reversa (forward/backward), formato de tensores e fluxo de gradientes nos 11 modelos MARKVART™.
- **Testes de Integração (`tests/integration/`)**: Fluxo ponta a ponta desde os adaptadores de ingestão até a saída no streamer gRPC.
- **Testes de IPC (`tests/ipc/`)**: Estresse do protocolo JSON-RPC via Stdio contra mensagens malformadas e rajadas concorrentes.
- **Benchmarks (`tests/benchmarks/`)**: Aferição da latência de ciclo de inferência, perfilamento de memória e taxa de serialização.

---

## 2. Executando os Testes

Ative o ambiente virtual antes da execução:

```bash
source .venv/bin/activate
```

### Executar Toda a Suíte Pytest:
```bash
pytest tests/ -v
```

### Executar com Análise de Cobertura:
```bash
pytest --cov=src --cov-report=term-missing --cov-report=html tests/
```

### Executar Apenas Testes de Modelos Neurais:
```bash
pytest tests/test_neural_models.py -v
```

---

## 3. Gerador de Tráfego Sintético e Mocks Determinísticos

Para viabilizar testes contínuos em ambientes isolados sem acesso a radares físicos:

- **`SyntheticTrafficGenerator`**: Simula dinâmicas realistas de veículos com base nas equações de onda de choque de Greenshields.
- **`MockHftReceiver`**: Servidor gRPC simulado em memória que recebe os snapshots e valida conformidade de esquema e latência.
- **Sementes Determinísticas**: Todas as rotinas de teste fixam sementes aleatórias (`torch.manual_seed(42)`) para garantir reprodutibilidade exata.

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
