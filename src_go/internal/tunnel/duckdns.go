// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

package tunnel

import (
	"context"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/url"
	"os"
	"strings"
	"sync"
	"time"

	"synapse-gateway/internal/domain"
	"synapse-gateway/internal/transport/pipe"
)

const (
	defaultDuckDNSRefreshInterval = 10 * time.Minute
	duckDNSUpdateEndpoint         = "https://www.duckdns.org/update"
)

// DuckDNSDriver handles periodic registration of IPv4/IPv6 with DuckDNS and IPC notifications.
type DuckDNSDriver struct {
	mu              sync.RWMutex
	httpClient      *http.Client
	pipeCtrl        *pipe.Controller
	updateURL       string
	refreshInterval time.Duration

	subdomain   string
	token       string
	port        string
	publicURL   string
	ipv6Address string
	isRunning   bool

	cancel context.CancelFunc
	doneCh chan struct{}
	logger *log.Logger
}

// NewDuckDNSDriver creates a new DuckDNSDriver linked to the pipe controller.
func NewDuckDNSDriver(pipeCtrl *pipe.Controller) *DuckDNSDriver {
	return &DuckDNSDriver{
		httpClient:      &http.Client{Timeout: 10 * time.Second},
		pipeCtrl:        pipeCtrl,
		updateURL:       duckDNSUpdateEndpoint,
		refreshInterval: defaultDuckDNSRefreshInterval,
		ipv6Address:     DetectGlobalIPv6(),
		logger:          log.New(os.Stderr, "[synapse-go-duckdns] ", log.Ltime|log.Lmicroseconds),
	}
}

// Start launches the DuckDNS periodic updater for the provided configuration.
func (d *DuckDNSDriver) Start(subdomain, token, port string) error {
	d.mu.Lock()
	defer d.mu.Unlock()

	cleanToken := CleanDuckDNSToken(token)
	if cleanToken == "" {
		return fmt.Errorf("duckdns token is required")
	}

	cleanSub := CleanDuckDNSDomain(subdomain)
	if cleanSub == "" {
		return fmt.Errorf("duckdns subdomain is required")
	}

	if port == "" {
		port = "8081"
	}

	// Terminate any previous execution
	if d.cancel != nil {
		d.cancel()
		d.cancel = nil
	}

	ctx, cancel := context.WithCancel(context.Background())
	d.cancel = cancel
	d.doneCh = make(chan struct{})
	d.token = cleanToken
	d.subdomain = cleanSub
	d.port = port
	d.isRunning = true

	// 1. Detect IPv6
	ipv6 := DetectGlobalIPv6()
	d.ipv6Address = ipv6
	if ipv6 != "" {
		d.logger.Printf("Detected public global IPv6: %s", ipv6)
	} else {
		d.logger.Printf("No public global IPv6 found. Operating in IPv4 mode.")
	}

	// 2. Perform initial synchronous update
	if err := d.executeUpdate(ctx, cleanSub, cleanToken, ipv6); err != nil {
		cancel()
		close(d.doneCh)
		d.isRunning = false
		d.emitStatus("ERROR", fmt.Sprintf("Failed initial DuckDNS update: %v", err))
		return fmt.Errorf("failed initial duckdns update: %w", err)
	}

	d.publicURL = fmt.Sprintf("https://%s.duckdns.org", cleanSub)
	d.logger.Printf("Successfully registered domain '%s.duckdns.org' -> %s", cleanSub, d.publicURL)
	d.emitStatus("ONLINE", fmt.Sprintf("DuckDNS Ativo: %s", d.publicURL))

	// 3. Launch periodic updater loop
	go d.loop(ctx, cleanSub, cleanToken)

	return nil
}

// Stop terminates the periodic background updater.
func (d *DuckDNSDriver) Stop() error {
	d.mu.Lock()
	defer d.mu.Unlock()

	if d.cancel != nil {
		d.cancel()
		d.cancel = nil
	}
	d.isRunning = false
	d.publicURL = ""
	d.logger.Println("DuckDNS updater stopped.")
	d.emitStatus("DISCONNECTED", "DuckDNS desconectado")
	return nil
}

// TestConnection executes an immediate probe against the DuckDNS API and emits the test result.
func (d *DuckDNSDriver) TestConnection(subdomain, token string) {
	cleanToken := CleanDuckDNSToken(token)
	cleanSub := CleanDuckDNSDomain(subdomain)

	if cleanToken == "" || cleanSub == "" {
		d.emitTestResult("ERROR", cleanSub, "Subdomínio e Token são obrigatórios para o teste.", 0)
		return
	}

	start := time.Now()
	ctx, cancel := context.WithTimeout(context.Background(), 8*time.Second)
	defer cancel()

	ipv6 := DetectGlobalIPv6()
	err := d.executeUpdate(ctx, cleanSub, cleanToken, ipv6)
	latency := time.Since(start).Milliseconds()

	if err != nil {
		d.emitTestResult("ERROR", cleanSub, fmt.Sprintf("Falha ao comunicar com DuckDNS: %v", err), latency)
		return
	}

	msg := fmt.Sprintf("Conexão validada com sucesso! Latência: %d ms. Domínio: %s.duckdns.org", latency, cleanSub)
	if ipv6 != "" {
		msg += fmt.Sprintf(" (IPv6 detectado: %s)", ipv6)
	}
	d.emitTestResult("OK", cleanSub, msg, latency)
}

func (d *DuckDNSDriver) executeUpdate(ctx context.Context, subdomain, token, ipv6 string) error {
	params := url.Values{}
	params.Set("domains", subdomain)
	params.Set("token", token)
	params.Set("ip", "") // Leave empty so DuckDNS detects public IPv4 automatically
	if ipv6 != "" {
		params.Set("ipv6", ipv6)
	}

	reqURL := fmt.Sprintf("%s?%s", d.updateURL, params.Encode())
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, reqURL, nil)
	if err != nil {
		return fmt.Errorf("failed to create duckdns request: %w", err)
	}

	resp, err := d.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("http request error: %w", err)
	}
	defer resp.Body.Close()

	bodyBytes, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("failed reading duckdns response: %w", err)
	}

	body := strings.TrimSpace(string(bodyBytes))
	if !strings.EqualFold(body, "OK") {
		return fmt.Errorf("duckdns rejected update (response: '%s'). Verifique o Token e o Subdomínio", body)
	}

	return nil
}

func (d *DuckDNSDriver) loop(ctx context.Context, subdomain, token string) {
	ticker := time.NewTicker(d.refreshInterval)
	defer func() {
		ticker.Stop()
		close(d.doneCh)
	}()

	for {
		select {
		case <-ctx.Done():
			d.logger.Println("Updater heartbeat loop terminated.")
			return
		case <-ticker.C:
			ipv6 := DetectGlobalIPv6()
			d.mu.Lock()
			d.ipv6Address = ipv6
			d.mu.Unlock()

			if err := d.executeUpdate(ctx, subdomain, token, ipv6); err != nil {
				d.logger.Printf("Periodic update warning: %v", err)
				d.emitStatus("WARNING", fmt.Sprintf("Aviso no batimento DuckDNS: %v", err))
			} else {
				d.logger.Printf("Periodic heartbeat refreshed successfully (%s.duckdns.org).", subdomain)
			}
		}
	}
}

func (d *DuckDNSDriver) emitStatus(status, message string) {
	if d.pipeCtrl == nil {
		return
	}
	_ = d.pipeCtrl.EmitMessage(domain.IPCMessage{
		Event:   "DUCKDNS_STATUS",
		Status:  status,
		Domain:  d.subdomain,
		Message: message,
	})
}

func (d *DuckDNSDriver) emitTestResult(status, domainName, message string, latencyMs int64) {
	if d.pipeCtrl == nil {
		return
	}
	_ = d.pipeCtrl.EmitMessage(domain.IPCMessage{
		Event:     "DUCKDNS_TEST_RESULT",
		Status:    status,
		Domain:    domainName,
		Message:   message,
		LatencyMs: latencyMs,
	})
}
