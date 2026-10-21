// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

package http

import (
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"strings"
)

func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write([]byte(`{"status":"HEALTHY","service":"synapse-go-gateway"}`))
}

func (s *Server) handleMetrics(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_ = s.pipe.EmitStats()
	_, _ = w.Write([]byte(`{"status":"OK"}`))
}

func (s *Server) handleRootOrSource(w http.ResponseWriter, r *http.Request) {
	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusNoContent)
		return
	}

	if r.Method != http.MethodPost {
		http.Error(w, `{"error":"Method Not Allowed. Use POST for sensor telemetry."}`, http.StatusMethodNotAllowed)
		return
	}

	path := strings.Trim(r.URL.Path, "/")
	if path == "" {
		s.handleGenericIngest(w, r)
		return
	}

	sourceID := path
	s.processIngestion(w, r, sourceID)
}

func (s *Server) handleGenericIngest(w http.ResponseWriter, r *http.Request) {
	if r.Method == http.MethodOptions {
		w.WriteHeader(http.StatusNoContent)
		return
	}

	if r.Method != http.MethodPost {
		http.Error(w, `{"error":"Method Not Allowed. Use POST."}`, http.StatusMethodNotAllowed)
		return
	}

	sourceID := r.URL.Query().Get("source_id")
	if sourceID == "" {
		sourceID = r.Header.Get("X-Sensor-ID")
	}
	if sourceID == "" {
		sourceID = r.Header.Get("X-Source-ID")
	}

	s.processIngestion(w, r, sourceID)
}

func (s *Server) processIngestion(w http.ResponseWriter, r *http.Request, sourceID string) {
	if !s.auth.Validate(r) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusUnauthorized)
		_, _ = w.Write([]byte(`{"error":"Unauthorized. Invalid or missing API Key."}`))
		return
	}

	r.Body = http.MaxBytesReader(w, r.Body, s.cfg.MaxPayloadSize)
	body, err := io.ReadAll(r.Body)
	if err != nil {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusBadRequest)
		_, _ = w.Write([]byte(fmt.Sprintf(`{"error":"Failed to read request body: %s"}`, err.Error())))
		return
	}

	if len(body) == 0 {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusBadRequest)
		_, _ = w.Write([]byte(`{"error":"Empty request body"}`))
		return
	}

	contentType := r.Header.Get("Content-Type")
	normalizedBody := body

	if sourceID == "" {
		sourceID = s.extractSourceFromJSON(body)
	}
	if sourceID == "" {
		sourceID = "unknown_sensor"
	}

	if !json.Valid(body) {
		escaped, _ := json.Marshal(string(body))
		normalizedBody = escaped
	}

	clientIP := s.extractClientIP(r)

	if err := s.pipe.EmitPacket(sourceID, normalizedBody, clientIP, contentType); err != nil {
		s.logger.Printf("Failed to emit packet to STDOUT pipe: %v", err)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusInternalServerError)
		_, _ = w.Write([]byte(`{"error":"Internal IPC Dispatch Failure"}`))
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write([]byte(fmt.Sprintf(`{"status":"ACCEPTED","source_id":"%s"}`, sourceID)))
}

func (s *Server) extractClientIP(r *http.Request) string {
	if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
		parts := strings.Split(xff, ",")
		return strings.TrimSpace(parts[0])
	}
	if xri := r.Header.Get("X-Real-IP"); xri != "" {
		return strings.TrimSpace(xri)
	}

	host, _, err := net.SplitHostPort(r.RemoteAddr)
	if err == nil {
		return host
	}
	return r.RemoteAddr
}

func (s *Server) extractSourceFromJSON(body []byte) string {
	var obj map[string]any
	if err := json.Unmarshal(body, &obj); err != nil {
		return ""
	}

	candidates := []string{"sensor_id", "source_id", "id", "camera_id", "device_id"}
	for _, key := range candidates {
		if val, exists := obj[key]; exists {
			if strVal, ok := val.(string); ok && strVal != "" {
				return strVal
			}
		}
	}
	return ""
}
