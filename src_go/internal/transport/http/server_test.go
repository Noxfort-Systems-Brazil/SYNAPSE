// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

package http

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"synapse-gateway/internal/config"
	"synapse-gateway/internal/domain"
	"synapse-gateway/internal/security"
	"synapse-gateway/internal/transport/pipe"
)

func TestServer_Endpoints(t *testing.T) {
	var stdout bytes.Buffer
	ctrl := pipe.NewController(strings.NewReader(""), &stdout, nil)
	cfg := &config.Config{
		Host:           "127.0.0.1",
		Port:           0,
		APIKey:         "secret-key-42",
		MaxPayloadSize: 10 * 1024 * 1024,
	}
	auth := security.NewAuthenticator(cfg.APIKey)
	server := NewServer(cfg, auth, ctrl)

	// 1. Health
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	w := httptest.NewRecorder()
	server.handleHealth(w, req)
	if w.Result().StatusCode != http.StatusOK {
		t.Errorf("expected 200 for /health, got %d", w.Result().StatusCode)
	}

	// 2. Unauthorized
	req = httptest.NewRequest(http.MethodPost, "/src_test", strings.NewReader(`{"test":1}`))
	w = httptest.NewRecorder()
	server.handleRootOrSource(w, req)
	if w.Result().StatusCode != http.StatusUnauthorized {
		t.Errorf("expected 401 Unauthorized, got %d", w.Result().StatusCode)
	}

	// 3. Authorized POST
	req = httptest.NewRequest(http.MethodPost, "/src_cam_77", strings.NewReader(`{"speed":80}`))
	req.Header.Set("Authorization", "Bearer secret-key-42")
	req.Header.Set("Content-Type", "application/json")
	w = httptest.NewRecorder()
	server.handleRootOrSource(w, req)
	if w.Result().StatusCode != http.StatusOK {
		t.Errorf("expected 200 OK for authorized POST, got %d", w.Result().StatusCode)
	}

	// Verify STDOUT
	var msg domain.IPCMessage
	if err := json.Unmarshal([]byte(stdout.String()), &msg); err != nil {
		t.Fatalf("failed to unmarshal STDOUT packet: %v", err)
	}
	if msg.Event != "PACKET" || msg.SourceID != "src_cam_77" {
		t.Errorf("unexpected STDOUT packet: %+v", msg)
	}
}
