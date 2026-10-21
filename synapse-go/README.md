# ⚡ SYNAPSE Ingestion Gateway (`synapse-go`)

High-Throughput Edge Sensor & Camera Ingestion Daemon engineered in **Go 1.22+**.  
Designed to absorb telemetry from thousands of concurrent roadside units, edge AI cameras, induction loops, and radar stations with sub-millisecond latency.

---

## 🏛️ Architecture & Clean Layout

Following the canonical **Standard Go Project Layout** (`cmd/`, `internal/`):

```
synapse-go/
├── cmd/
│   └── gateway/
│       └── main.go               # Orchestrator & Application Entrypoint
├── internal/
│   ├── config/
│   │   ├── config.go             # Environment & CLI Flags Configuration
│   │   └── config_test.go        # Configuration Unit Tests
│   ├── domain/
│   │   └── telemetry.go          # Core Data Schemas & IPC Protocols
│   ├── security/
│   │   ├── auth.go               # Bearer Token & X-API-Key Validator
│   │   └── auth_test.go          # Security Unit Tests
│   └── transport/
│       ├── http/
│       │   ├── server.go         # HTTP Server Lifecycle & Graceful Teardown
│       │   ├── handlers.go       # High-Throughput REST Ingestion Handlers
│       │   ├── middleware.go     # Permissive Industrial CORS Headers
│       │   └── server_test.go    # HTTP Handlers Unit Tests
│       └── pipe/
│           ├── controller.go     # Thread-Safe STDOUT Broadcaster & STDIN Scanner
│           └── controller_test.go# Anonymous Pipe Lifecycle Tests
├── Makefile                      # Standard Build Automation
└── go.mod                        # Go Module Definition
```

---

## 🔒 Zero-Port OS Anonymous Pipe IPC

Unlike traditional Unix Domain Sockets that create `.sock` files on the filesystem, or internal TCP loopback servers that risk port collisions (`[Errno 98]`), `synapse-go` communicates with the parent Python process exclusively via **Anonymous Kernel Pipes (`STDIN`/`STDOUT`)**:

* **`STDOUT` (Go ➔ Python):** Pure sensor telemetry formatted as NDJSON (*Newline-Delimited JSON*).
* **`STDIN` (Python ➔ Go):** Bidirectional control commands (`PING`, `GET_STATS`, `SHUTDOWN`).
* **`STDERR` (Go ➔ Python Logger):** Operational diagnostics and warnings routed to the central Python logging facade.
* **Auto-Cleanup on Exit:** If the Python parent terminates, `os.Stdin` encounters `EOF`, causing `synapse-go` to shut down gracefully without leaving orphan or zombie processes.

---

## 🛠️ Build & Test Commands

```bash
# Run all unit tests with race detection
make test

# Compile binary to bin/synapse-gateway
make build

# Run standalone for development testing
make run
```

---

<div align="center">
  <img src="../docs/assets/noxfort-logo.png" alt="Noxfort Systems Logo" width="48" /><br/>
  <b>Noxfort Systems</b> — <i>A State Of Art Company</i><br/>
  <i>Intelligent Perception & Neural Fusion Gateway • SYNAPSE CORE v2.0</i><br/>
  <small>SPDX-License-Identifier: <a href="../LICENSE"><code>AGPL-3.0-or-later</code></a> • © 2026 Noxfort Systems</small>
</div>
