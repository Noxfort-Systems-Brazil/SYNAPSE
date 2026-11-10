// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

package poller

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync"
	"testing"
	"time"

	"synapse-gateway/internal/domain"
	"synapse-gateway/internal/transport/pipe"
)

type safeBuffer struct {
	mu  sync.Mutex
	buf bytes.Buffer
}

func (s *safeBuffer) Write(p []byte) (n int, err error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.buf.Write(p)
}

func (s *safeBuffer) String() string {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.buf.String()
}

func TestPoller_FetchAndEmit(t *testing.T) {
	// Mock HTTP Server simulating external traffic API (e.g. Waze)
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"alerts":[{"type":"JAM","speed":15.0}]}`))
	}))
	defer server.Close()

	var stdout safeBuffer
	ctrl := pipe.NewController(strings.NewReader(""), &stdout, nil)
	p := NewPoller(ctrl)
	defer p.StopAll()

	p.Register("waze_test", server.URL, 0.1) // 100ms interval

	time.Sleep(150 * time.Millisecond)
	p.StopAll()

	output := stdout.String()
	if !strings.Contains(output, "waze_test") {
		t.Fatalf("expected stdout to contain polled packet for waze_test, got: %s", output)
	}

	lines := strings.Split(strings.TrimSpace(output), "\n")
	var msg domain.IPCMessage
	if err := json.Unmarshal([]byte(lines[0]), &msg); err != nil {
		t.Fatalf("failed to unmarshal polled packet: %v", err)
	}

	if msg.SourceID != "waze_test" {
		t.Errorf("expected SourceID=waze_test, got %s", msg.SourceID)
	}
}
