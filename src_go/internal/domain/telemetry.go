// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

package domain

import "encoding/json"

// IPCMessage represents outgoing JSON messages to Python via STDOUT pipe.
type IPCMessage struct {
	Event       string          `json:"event"`
	SourceID    string          `json:"source_id,omitempty"`
	Payload     json.RawMessage `json:"payload,omitempty"`
	ClientIP    string          `json:"client_ip,omitempty"`
	Timestamp   float64         `json:"timestamp,omitempty"`
	Transport   string          `json:"transport,omitempty"`
	ContentType string          `json:"content_type,omitempty"`
	Status       string          `json:"status,omitempty"`
	Error        string          `json:"error,omitempty"`
	Message      string          `json:"message,omitempty"`
	Domain       string          `json:"domain,omitempty"`
	Stats        *GatewayStats   `json:"stats,omitempty"`
	ClientConfig string          `json:"client_config,omitempty"`
	PublicKey    string          `json:"public_key,omitempty"`
	CaddyRunning bool            `json:"caddy_running,omitempty"`
	CaddyPort    int             `json:"caddy_port,omitempty"`
	LatencyMs    int64           `json:"latency_ms,omitempty"`
	PublicURL    string          `json:"public_url,omitempty"`
}

// IPCCommand represents incoming JSON commands from Python via STDIN pipe.
type IPCCommand struct {
	Cmd          string  `json:"cmd"`
	APIKey       string  `json:"api_key,omitempty"`
	LogLevel     string  `json:"log_level,omitempty"`
	SourceID     string  `json:"source_id,omitempty"`
	URL          string  `json:"url,omitempty"`
	IntervalSec  float64 `json:"interval_sec,omitempty"`
	Topic        string  `json:"topic,omitempty"`
	PeerID       string  `json:"peer_id,omitempty"`
	Domain       string  `json:"domain,omitempty"`
	Token        string  `json:"token,omitempty"`
	Port         string  `json:"port,omitempty"`
	Enabled      bool    `json:"enabled,omitempty"`
	CaddyEnabled bool    `json:"caddy_enabled,omitempty"`
	HTTPSPort    int     `json:"https_port,omitempty"`
}

// GatewayStats holds operational metrics.
type GatewayStats struct {
	TotalRequests uint64  `json:"total_requests"`
	TotalBytes    uint64  `json:"total_bytes"`
	UptimeSec     float64 `json:"uptime_sec"`
}
