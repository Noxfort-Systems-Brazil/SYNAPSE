// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

package http

import (
	"context"
	"errors"
	"fmt"
	"log"
	"net"
	"net/http"
	"os"
	"sync"
	"time"

	"synapse-gateway/internal/config"
	"synapse-gateway/internal/security"
	"synapse-gateway/internal/transport/pipe"
)

// Server coordinates HTTP ingestion and dispatches packets to the PipeController.
type Server struct {
	cfg     *config.Config
	auth    *security.Authenticator
	pipe    *pipe.Controller
	server  *http.Server
	logger  *log.Logger
	mu      sync.RWMutex
	running bool
}

// NewServer constructs the Server instance with injected dependencies.
func NewServer(cfg *config.Config, auth *security.Authenticator, p *pipe.Controller) *Server {
	return &Server{
		cfg:    cfg,
		auth:   auth,
		pipe:   p,
		logger: log.New(os.Stderr, "[synapse-go-http] ", log.Ltime|log.Lmicroseconds),
	}
}

// Start boots the HTTP server asynchronously on the configured host and port.
func (s *Server) Start() error {
	s.mu.Lock()
	if s.running {
		s.mu.Unlock()
		return nil
	}

	addr := fmt.Sprintf("%s:%d", s.cfg.Host, s.cfg.Port)
	mux := http.NewServeMux()

	mux.HandleFunc("/", s.handleRootOrSource)
	mux.HandleFunc("/health", s.handleHealth)
	mux.HandleFunc("/metrics", s.handleMetrics)
	mux.HandleFunc("/api/v1/telemetry", s.handleGenericIngest)
	mux.HandleFunc("/ingest", s.handleGenericIngest)

	s.server = &http.Server{
		Addr:              addr,
		Handler:           CORSMiddleware(mux),
		ReadTimeout:       s.cfg.ReadTimeout,
		ReadHeaderTimeout: 5 * time.Second,
		WriteTimeout:      s.cfg.WriteTimeout,
		IdleTimeout:       s.cfg.IdleTimeout,
	}

	ln, err := net.Listen("tcp", addr)
	if err != nil {
		s.mu.Unlock()
		return fmt.Errorf("failed to bind HTTP gateway on %s: %w", addr, err)
	}

	s.running = true
	s.mu.Unlock()

	s.logger.Printf("🚀 High-Throughput Sensor Ingestion Gateway listening on http://%s", addr)
	_ = s.pipe.EmitEvent("GATEWAY_ONLINE", "LISTENING", fmt.Sprintf("http://%s", addr))

	go func() {
		if err := s.server.Serve(ln); err != nil && !errors.Is(err, http.ErrServerClosed) {
			s.logger.Printf("HTTP Gateway server error: %v", err)
			_ = s.pipe.EmitEvent("GATEWAY_ERROR", "ERROR", err.Error())
		}
	}()

	return nil
}

// Stop gracefully shuts down the HTTP server.
func (s *Server) Stop(ctx context.Context) error {
	s.mu.Lock()
	defer s.mu.Unlock()

	if !s.running || s.server == nil {
		return nil
	}

	s.running = false
	s.logger.Println("Shutting down HTTP Gateway listener...")
	return s.server.Shutdown(ctx)
}
