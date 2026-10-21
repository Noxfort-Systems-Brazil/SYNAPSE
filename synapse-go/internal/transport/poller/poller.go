// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

package poller

import (
	"context"
	"encoding/json"
	"io"
	"log"
	"net/http"
	"os"
	"sync"
	"time"

	"synapse-gateway/internal/transport/pipe"
)

type pollJob struct {
	sourceID string
	url      string
	interval time.Duration
	stopCh   chan struct{}
}

// Poller manages concurrent periodic HTTP GET requests to external REST APIs.
type Poller struct {
	pipe       *pipe.Controller
	httpClient *http.Client
	jobs       map[string]*pollJob
	mu         sync.RWMutex
	logger     *log.Logger
	stopCh     chan struct{}
	stopped    bool
}

// NewPoller initializes the HTTP Poller engine.
func NewPoller(p *pipe.Controller) *Poller {
	return &Poller{
		pipe: p,
		httpClient: &http.Client{
			Timeout: 12 * time.Second,
		},
		jobs:   make(map[string]*pollJob),
		logger: log.New(os.Stderr, "[synapse-go-poller] ", log.Ltime|log.Lmicroseconds),
		stopCh: make(chan struct{}),
	}
}

// Register registers or updates a periodic polling job for an external API.
func (p *Poller) Register(sourceID, rawURL string, intervalSec float64) {
	if sourceID == "" || rawURL == "" {
		return
	}

	if intervalSec <= 0 {
		intervalSec = 10.0 // Default to 10s
	}
	interval := time.Duration(intervalSec * float64(time.Second))

	p.mu.Lock()
	defer p.mu.Unlock()

	if p.stopped {
		return
	}

	// If already registered with same URL & interval, do nothing
	if existing, found := p.jobs[sourceID]; found {
		if existing.url == rawURL && existing.interval == interval {
			return
		}
		// Cancel old job
		close(existing.stopCh)
	}

	job := &pollJob{
		sourceID: sourceID,
		url:      rawURL,
		interval: interval,
		stopCh:   make(chan struct{}),
	}
	p.jobs[sourceID] = job

	p.logger.Printf("🌐 Registered poll target '%s' -> %s [interval=%v]", sourceID, rawURL, interval)
	go p.runJob(job)
}

// Unregister cancels and removes a polling job.
func (p *Poller) Unregister(sourceID string) {
	p.mu.Lock()
	defer p.mu.Unlock()

	if job, found := p.jobs[sourceID]; found {
		close(job.stopCh)
		delete(p.jobs, sourceID)
		p.logger.Printf("🛑 Unregistered poll target '%s'", sourceID)
	}
}

// StopAll gracefully cancels all active polling goroutines.
func (p *Poller) StopAll() {
	p.mu.Lock()
	defer p.mu.Unlock()

	if p.stopped {
		return
	}
	p.stopped = true
	close(p.stopCh)

	for id, job := range p.jobs {
		close(job.stopCh)
		delete(p.jobs, id)
	}
	p.logger.Println("All polling jobs terminated.")
}

func (p *Poller) runJob(job *pollJob) {
	// Immediate first fetch
	p.fetchOne(job)

	ticker := time.NewTicker(job.interval)
	defer ticker.Stop()

	for {
		select {
		case <-job.stopCh:
			return
		case <-p.stopCh:
			return
		case <-ticker.C:
			p.fetchOne(job)
		}
	}
}

func (p *Poller) fetchOne(job *pollJob) {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, job.url, nil)
	if err != nil {
		p.logger.Printf("⚠️ Invalid request for '%s': %v", job.sourceID, err)
		return
	}
	req.Header.Set("User-Agent", "Synapse-Go-Poller/1.0")
	req.Header.Set("Accept", "application/json, text/csv, */*")

	resp, err := p.httpClient.Do(req)
	if err != nil {
		p.logger.Printf("⚠️ Fetch error for '%s' (%s): %v", job.sourceID, job.url, err)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		p.logger.Printf("⚠️ Non-2xx status code %d for '%s' (%s)", resp.StatusCode, job.sourceID, job.url)
		return
	}

	body, err := io.ReadAll(io.LimitReader(resp.Body, 10*1024*1024))
	if err != nil || len(body) == 0 {
		return
	}

	normalized := body
	if !json.Valid(body) {
		escaped, _ := json.Marshal(string(body))
		normalized = escaped
	}

	contentType := resp.Header.Get("Content-Type")
	if err := p.pipe.EmitPacket(job.sourceID, normalized, job.url, contentType); err != nil {
		p.logger.Printf("Failed to emit polled packet to pipe: %v", err)
	}
}
