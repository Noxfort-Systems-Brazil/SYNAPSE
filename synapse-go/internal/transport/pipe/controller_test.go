// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

package pipe

import (
	"bytes"
	"encoding/json"
	"strings"
	"testing"

	"synapse-gateway/internal/domain"
)

func TestController_EmitPacket(t *testing.T) {
	var stdout bytes.Buffer
	stdin := strings.NewReader("")

	ctrl := NewController(stdin, &stdout, nil)

	payload := []byte(`{"speed":75.2,"vehicle_count":12}`)
	err := ctrl.EmitPacket("sensor_01", payload, "192.168.1.100", "application/json")
	if err != nil {
		t.Fatalf("unexpected error emitting packet: %v", err)
	}

	output := stdout.String()
	if !strings.HasSuffix(output, "\n") {
		t.Fatalf("expected output to end with newline (NDJSON), got: %s", output)
	}

	var msg domain.IPCMessage
	if err := json.Unmarshal([]byte(output), &msg); err != nil {
		t.Fatalf("failed to parse output as JSON: %v", err)
	}

	if msg.Event != "PACKET" {
		t.Errorf("expected Event=PACKET, got %s", msg.Event)
	}
	if msg.SourceID != "sensor_01" {
		t.Errorf("expected SourceID=sensor_01, got %s", msg.SourceID)
	}
	if msg.ClientIP != "192.168.1.100" {
		t.Errorf("expected ClientIP=192.168.1.100, got %s", msg.ClientIP)
	}
}

func TestController_CommandLoop(t *testing.T) {
	var stdout bytes.Buffer
	stdin := strings.NewReader("{\"cmd\":\"PING\"}\n{\"cmd\":\"GET_STATS\"}\n")

	stopped := false
	ctrl := NewController(stdin, &stdout, func() {
		stopped = true
	})

	ctrl.StartStdinLoop()

	if !stopped {
		t.Errorf("expected pipe to signal shutdown on EOF")
	}

	lines := strings.Split(strings.TrimSpace(stdout.String()), "\n")
	if len(lines) < 2 {
		t.Fatalf("expected at least 2 responses, got %d lines: %v", len(lines), lines)
	}

	var pong domain.IPCMessage
	if err := json.Unmarshal([]byte(lines[0]), &pong); err != nil {
		t.Fatalf("failed to unmarshal PONG: %v", err)
	}
	if pong.Event != "PONG" || pong.Status != "OK" {
		t.Errorf("unexpected PONG response: %+v", pong)
	}
}
