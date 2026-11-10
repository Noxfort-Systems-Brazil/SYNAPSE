# 🖥️ SYNAPSE: Arquitetura UI e IPC Stdio de Porta Zero

Este documento especifica a arquitetura da interface desktop do SYNAPSE, abrangendo o hospedeiro nativo Rust em Tauri v2, a aplicação React 18, as stores reativas Zustand e o canal IPC Stdio JSON-RPC sem abertura de portas de rede.

⬅️ [Central de Documentação](README.md) | ⚡ [Ingestão e HFT](data_ingestion_and_hft.md) | 🛡️ [Segurança e Watchdog](safety_and_watchdog.md)

---

## 1. Visão Geral e Segurança de Porta Zero

Para atender aos rígidos requisitos de segurança de salas de controle de tráfego, o SYNAPSE não expõe portas HTTP ou WebSockets em `localhost`. O aplicativo desktop comunica-se com o backend Python através de pipes padrão do sistema operacional com mensagens JSON-RPC delimitadas por nova linha:

```
┌────────────────────────────────────────────────────────┐
│                   APLICAÇÃO DESKTOP TAURI v2           │
│                                                        │
│   ┌────────────────────────────────────────────────┐   │
│   │                 REACT 18 SPA                   │   │
│   │  - Stores Reativas Zustand                     │   │
│   │  - Tailwind CSS + Ícones Lucide                │   │
│   │  - Visualizações em Tempo Real com ECharts     │   │
│   └───────────────────────┬────────────────────────┘   │
│                           │ Comandos Invoke do Tauri   │
│   ┌───────────────────────▼────────────────────────┐   │
│   │               RUST CORE (src-tauri)            │   │
│   │  - Gestor de Processos Filhos (Inicia Python)  │   │
│   │  - Interceptador Não-Bloqueante de Pipes Stdio │   │
│   └───────────────────────┬────────────────────────┘   │
└───────────────────────────┼────────────────────────────┘
                            │ STDIN / STDOUT (JSON-RPC)
┌───────────────────────────▼────────────────────────────┐
│              BACKEND PYTHON (StdioDaemon)              │
│  - CommandRouter, IpcEventBridge, Motor PyTorch        │
└────────────────────────────────────────────────────────┘
```

---

## 2. Gerenciamento de Estado com Zustand

A interface utiliza stores modulares **Zustand** para manter alta responsividade:

- **`useSensorsStore`**: Rastreia sensores ativos, taxa de pacotes, scores Bayesianos de confiança e status (`ACTIVE`, `QUARANTINE`, `FALLBACK`).
- **`useTopologyStore`**: Gerencia o grafo carregado ($V, E$), coordenadas geográficas e capacidades de via.
- **`useSystemStore`**: Monitora uso de CPU/GPU, VRAM, latência de ciclo de inferência ($< 15\text{ ms}$) e saúde do supervisor F.E.N.I.X.
- **`useSecurityStore`**: Gerencia autenticação de operadores municipais, tokens de sessão, políticas de senha e bloqueios automáticos.
- **`useReportStore` & `useReportTypographyStore`**: Controla relatórios periciais de tráfego formatados segundo normas ABNT, com pré-visualização HTML e personalização tipográfica.
- **`useXaiStore`**: Armazena laudos gerados pelo Qwen3 Jurist e alertas de anomalias viárias.
- **`useEtlStore`**: Coordena o assistente de importação de arquivos Parquet (`ParquetImportModal`) e ingestão no Data Lake histórico.

---

## 3. Abas de Configuração e Painéis Operacionais

A interface gráfica moderna oferece abas especializadas para operação municipal:
- **`DuckDnsSettingsTab`**: Configura o domínio dinâmico e encaminhamento de porta HTTPS via túnel do Go Gateway e proxy Caddy.
- **`DatabaseSettingsTab`**: Valida a conexão com o PostgreSQL, ajusta parâmetros de pool de conexões e aplica migrações de esquema.
- **`MonitorSettingsTab`**: Ajusta as portas de exportação de métricas Prometheus e painéis de telemetria Grafana.
- **`AccountSettingsTab`**: Gerencia usuários operadores, níveis de permissão e redefinição de senhas.
- **`ParquetImportModal`**: Assistente interativo de 3 etapas para importação ETL com validação anti-arquivos fantasma.

---

## 3. Protocolo IPC Stdio JSON-RPC

A troca de mensagens segue o padrão JSON-RPC 2.0 assíncrono:

### Exemplo de Requisição (UI $\rightarrow$ Python):
```json
{
  "jsonrpc": "2.0",
  "id": "req-1042",
  "method": "get_topology_snapshot",
  "params": {
    "include_metrics": true
  }
}
```

### Exemplo de Evento Emitido (Python $\rightarrow$ UI via STDOUT):
```json
{
  "jsonrpc": "2.0",
  "method": "on_telemetry_tick",
  "params": {
    "timestamp_ns": 1774728190000000,
    "active_sensors": 48,
    "mean_trust_score": 0.942,
    "hft_latency_ms": 1.2
  }
}
```

---

<div align="center">
  <img src="../assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
