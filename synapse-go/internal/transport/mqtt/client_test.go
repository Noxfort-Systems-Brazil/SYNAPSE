// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

package mqtt

import (
	"bytes"
	"strings"
	"testing"

	"synapse-gateway/internal/transport/pipe"
)

func TestClient_ResolveSourceID(t *testing.T) {
	var stdout bytes.Buffer
	ctrl := pipe.NewController(strings.NewReader(""), &stdout, nil)
	client := NewClient(Config{}, ctrl)

	// 1. Resolve from JSON origin
	id1 := client.resolveSourceID("noxfort/telemetry/events", []byte(`{"origin":"camera_01","speed":50}`))
	if id1 != "camera_01" {
		t.Errorf("expected camera_01, got %s", id1)
	}

	// 2. Resolve from JSON sensor_id
	id2 := client.resolveSourceID("synapse/data", []byte(`{"sensor_id":"radar_north","count":10}`))
	if id2 != "radar_north" {
		t.Errorf("expected radar_north, got %s", id2)
	}

	// 3. Fallback resolve from topic segment
	id3 := client.resolveSourceID("traffic/cameras/cam_highway_99/telemetry", []byte(`{"speed":70}`))
	if id3 != "cam_highway_99" {
		t.Errorf("expected cam_highway_99, got %s", id3)
	}
}
