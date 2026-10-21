// SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
// Copyright (C) 2026 Noxfort Systems
//
// File: synapse-go/internal/tunnel/caddy.go
// Author: Gabriel Moraes
// Description: Pure Go orchestrator for bundled Caddy reverse proxy process lifecycle (Clean Arch).

package tunnel

import (
	"bytes"
	"fmt"
	"log"
	"os"
	"os/exec"
	"strings"
	"sync"
	"syscall"
	"time"

	"synapse-gateway/internal/domain"
	"synapse-gateway/internal/transport/pipe"
)

// CaddyManager manages the lifecycle of the bundled Caddy reverse proxy process.
type CaddyManager struct {
	mu            sync.RWMutex
	binPath       string
	caddyfilePath string
	cmd           *exec.Cmd
	pipeCtrl      *pipe.Controller

	subdomain  string
	token      string
	targetPort int
	httpsPort  int
	activePort int
	isRunning  bool
	logger     *log.Logger
}

// NewCaddyManager creates a new Caddy process manager.
func NewCaddyManager(binPath, caddyfilePath string, pipeCtrl *pipe.Controller) *CaddyManager {
	if binPath == "" {
		binPath = ResolveDefaultCaddyPath()
	}
	if caddyfilePath == "" {
		caddyfilePath = ResolveDefaultCaddyfilePath()
	}

	return &CaddyManager{
		binPath:       binPath,
		caddyfilePath: caddyfilePath,
		pipeCtrl:      pipeCtrl,
		activePort:    443,
		logger:        log.New(os.Stderr, "[synapse-go-caddy] ", log.Ltime|log.Lmicroseconds),
	}
}

// GenerateCaddyfile creates a clean Caddyfile mapping the DuckDNS domain to the local Go Gateway.
func (c *CaddyManager) GenerateCaddyfile(subdomain string, targetPort, httpsPort int, token string) (string, error) {
	path, err := GenerateCaddyfileContent(c.caddyfilePath, subdomain, targetPort, httpsPort, token)
	if err == nil {
		c.logger.Printf("Generated Caddyfile for domain '%s.duckdns.org' (HTTPS: %d -> Local: %d)", subdomain, httpsPort, targetPort)
	}
	return path, err
}

// Start spawns the Caddy binary as a supervised child process of Go.
func (c *CaddyManager) Start(subdomain string, targetPort, httpsPort int, token string) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	if c.isRunning {
		c.logger.Println("Caddy is already running. Reloading configuration...")
		_ = c.stopLocked()
	}

	if _, err := os.Stat(c.binPath); err != nil {
		c.emitStatus("ERROR", fmt.Sprintf("Caddy binary not found at %s", c.binPath))
		return fmt.Errorf("caddy binary not found: %w", err)
	}

	if httpsPort <= 0 {
		httpsPort = 443
	}
	if targetPort <= 0 {
		targetPort = 8081
	}

	c.subdomain = CleanDuckDNSDomain(subdomain)
	c.token = CleanDuckDNSToken(token)
	c.targetPort = targetPort
	c.httpsPort = httpsPort
	c.activePort = httpsPort

	if _, err := c.GenerateCaddyfile(c.subdomain, c.targetPort, c.httpsPort, c.token); err != nil {
		c.emitStatus("ERROR", fmt.Sprintf("Failed to generate Caddyfile: %v", err))
		return err
	}

	return c.spawnWithFallback(c.httpsPort)
}

func (c *CaddyManager) spawnWithFallback(port int) error {
	cmd := exec.Command(c.binPath, "run", "--config", c.caddyfilePath, "--adapter", "caddyfile")
	var stderrBuf bytes.Buffer
	cmd.Stderr = &stderrBuf
	cmd.Stdout = nil

	c.logger.Printf("Starting Caddy daemon on port %d: %s", port, cmd.String())
	if err := cmd.Start(); err != nil {
		c.emitStatus("ERROR", fmt.Sprintf("Failed to spawn Caddy: %v", err))
		return fmt.Errorf("failed to spawn caddy: %w", err)
	}

	c.cmd = cmd

	errCh := make(chan error, 1)
	go func() {
		errCh <- cmd.Wait()
	}()

	select {
	case err := <-errCh:
		out := stderrBuf.String()
		c.logger.Printf("⚠️ Caddy exited early on port %d: %v (stderr: %s)", port, err, strings.TrimSpace(out))

		if port == 443 && (strings.Contains(strings.ToLower(out), "permission denied") || strings.Contains(strings.ToLower(out), "bind")) {
			c.logger.Println("🛡️ Falling back to unprivileged HTTPS port 8443...")
			c.activePort = 8443
			c.httpsPort = 8443
			_, _ = c.GenerateCaddyfile(c.subdomain, c.targetPort, 8443, c.token)
			return c.spawnWithFallback(8443)
		}

		c.isRunning = false
		c.cmd = nil
		c.emitStatus("ERROR", fmt.Sprintf("Caddy terminated on port %d: %s", port, strings.TrimSpace(out)))
		return fmt.Errorf("caddy exited early: %w", err)

	case <-time.After(800 * time.Millisecond):
		c.isRunning = true
		c.activePort = port
		c.logger.Printf("🛡️ Caddy Reverse Proxy ONLINE (HTTPS active on port %d).", port)
		c.emitStatus("ONLINE", fmt.Sprintf("Caddy HTTPS ativo na porta %d", port))

		go c.supervisorLoop(cmd, port, errCh)
		return nil
	}
}

func (c *CaddyManager) supervisorLoop(cmd *exec.Cmd, port int, errCh <-chan error) {
	err := <-errCh
	c.mu.Lock()
	defer c.mu.Unlock()

	if c.cmd == cmd {
		c.isRunning = false
		c.cmd = nil
		c.logger.Printf("Caddy process terminated (port %d): %v", port, err)
		c.emitStatus("DISCONNECTED", fmt.Sprintf("Caddy finalizado na porta %d", port))
	}
}

// Stop terminates the Caddy process gracefully.
func (c *CaddyManager) Stop() error {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.stopLocked()
}

func (c *CaddyManager) stopLocked() error {
	if !c.isRunning || c.cmd == nil || c.cmd.Process == nil {
		c.isRunning = false
		c.cmd = nil
		return nil
	}

	c.logger.Println("Stopping Caddy reverse proxy...")
	proc := c.cmd.Process

	_ = proc.Signal(syscall.SIGTERM)

	done := make(chan struct{})
	go func() {
		_, _ = proc.Wait()
		close(done)
	}()

	select {
	case <-done:
	case <-time.After(2 * time.Second):
		c.logger.Println("Caddy did not terminate within timeout; killing...")
		_ = proc.Kill()
		<-done
	}

	c.isRunning = false
	c.cmd = nil
	c.emitStatus("STOPPED", "Caddy parado com sucesso")
	return nil
}

// IsRunning returns whether the Caddy process is currently active.
func (c *CaddyManager) IsRunning() bool {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.isRunning
}

// ActivePort returns the HTTPS port Caddy is currently bound to.
func (c *CaddyManager) ActivePort() int {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.activePort
}

// PublicURL returns the complete HTTPS URL pointing to the reverse proxy.
func (c *CaddyManager) PublicURL() string {
	c.mu.RLock()
	defer c.mu.RUnlock()
	if c.subdomain == "" {
		return ""
	}
	if c.activePort == 443 {
		return fmt.Sprintf("https://%s.duckdns.org", c.subdomain)
	}
	return fmt.Sprintf("https://%s.duckdns.org:%d", c.subdomain, c.activePort)
}

func (c *CaddyManager) emitStatus(status, message string) {
	if c.pipeCtrl == nil {
		return
	}

	pubURL := ""
	if c.subdomain != "" && c.isRunning {
		if c.activePort == 443 {
			pubURL = fmt.Sprintf("https://%s.duckdns.org", c.subdomain)
		} else {
			pubURL = fmt.Sprintf("https://%s.duckdns.org:%d", c.subdomain, c.activePort)
		}
	}

	_ = c.pipeCtrl.EmitMessage(domain.IPCMessage{
		Event:        "CADDY_STATUS",
		Status:       status,
		Domain:       c.subdomain,
		Message:      message,
		CaddyRunning: c.isRunning,
		CaddyPort:    c.activePort,
		PublicURL:    pubURL,
	})
}
