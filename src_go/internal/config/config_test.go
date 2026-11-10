// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

package config

import (
	"testing"
)

func TestConfig_LoadWithDefaults(t *testing.T) {
	cfg := Load([]string{})
	if cfg.Host != "0.0.0.0" {
		t.Errorf("expected Host 0.0.0.0, got %s", cfg.Host)
	}
	if cfg.Port != 8081 {
		t.Errorf("expected Port 8081, got %d", cfg.Port)
	}
}

func TestConfig_LoadWithFlags(t *testing.T) {
	cfg := Load([]string{"-host", "127.0.0.1", "-port", "9090", "-api-key", "secret123"})
	if cfg.Host != "127.0.0.1" {
		t.Errorf("expected Host 127.0.0.1, got %s", cfg.Host)
	}
	if cfg.Port != 9090 {
		t.Errorf("expected Port 9090, got %d", cfg.Port)
	}
	if cfg.APIKey != "secret123" {
		t.Errorf("expected APIKey secret123, got %s", cfg.APIKey)
	}
}
