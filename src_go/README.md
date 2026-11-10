# ⚡ SYNAPSE Ingestion Gateway (`synapse-go`)

High-Throughput Edge Sensor & Camera Ingestion Daemon engineered in **Go 1.22+**.  
Designed to absorb telemetry from thousands of concurrent roadside units, edge AI cameras, induction loops, and radar stations with sub-millisecond latency.

---

## 🏛️ Architecture & Clean Layout

Following the canonical **Standard Go Project Layout** (`cmd/`, `internal/`):

```
src_go/
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
│   ├── transport/
│   │   ├── http/
│   │   │   ├── server.go         # HTTP Server Lifecycle & Graceful Teardown
│   │   │   ├── handlers.go       # High-Throughput REST Ingestion Handlers
│   │   │   ├── middleware.go     # Permissive Industrial CORS Headers
│   │   │   └── server_test.go    # HTTP Handlers Unit Tests
│   │   └── pipe/
│   │       ├── controller.go     # Thread-Safe STDOUT Broadcaster & STDIN Scanner
│   │       └── controller_test.go# Anonymous Pipe Lifecycle Tests
│   └── tunnel/
│       ├── duckdns.go            # Periodic Dynamic DNS (IPv4/IPv6) Updater
│       ├── duckdns_util.go       # Global IP Detection Utilities
│       ├── caddy.go              # Caddy Process Supervisor & Process Lifecycle
│       ├── caddyfile.go          # Dynamic Caddyfile Generation (Let's Encrypt TLS)
│       ├── duckdns_test.go       # DuckDNS Unit Tests
│       └── caddy_test.go         # Caddy Supervisor Unit Tests
├── Makefile                      # Standard Build Automation
└── go.mod                        # Go Module Definition
```

---

## 🌐 Secure Reverse Tunneling (DuckDNS & Caddy HTTPS)

`synapse-go` integrates autonomous public ingress tunneling to allow municipal cameras and field sensors to stream telemetry safely without requiring static public IPs or manual router port-forwarding:

1. **DuckDNS Driver (`internal/tunnel/duckdns.go`)**:
   - Detects public IPv4 and global IPv6 (`DetectGlobalIPv6`).
   - Automatically posts periodic heartbeat updates to `duckdns.org/update` every 10 minutes.
   - Dispatches status events over the anonymous pipe to Python (`DuckDnsHandler`).
2. **Caddy HTTPS Process Supervisor (`internal/tunnel/caddy.go`)**:
   - Manages the embedded [`bin/caddy`](../bin/caddy) process lifecycle.
   - Dynamically compiles [`config/Caddyfile`](../config/Caddyfile) binding to port 443 with automatic TLS provisioning (Let's Encrypt / ZeroSSL).
   - Terminates TLS at line rate and proxies payloads internally to the high-throughput Go ingestion server.

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
