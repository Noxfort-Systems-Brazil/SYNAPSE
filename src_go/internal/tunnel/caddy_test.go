// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

package tunnel

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestCaddyManagerGenerateCaddyfile(t *testing.T) {
	tempDir := t.TempDir()
	caddyfilePath := filepath.Join(tempDir, "Caddyfile")

	mgr := NewCaddyManager("dummy-bin", caddyfilePath, nil)

	// Test 1: Standard port 443 with DuckDNS token
	path, err := mgr.GenerateCaddyfile("https://curitiba-transito.duckdns.org/", 8081, 443, "tok_12345")
	if err != nil {
		t.Fatalf("expected generation to succeed, got %v", err)
	}

	content, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("failed reading generated caddyfile: %v", err)
	}

	strContent := string(content)
	if !strings.Contains(strContent, "curitiba-transito.duckdns.org {") {
		t.Errorf("expected site block 'curitiba-transito.duckdns.org {', got:\n%s", strContent)
	}
	if !strings.Contains(strContent, "dns duckdns tok_12345") {
		t.Errorf("expected duckdns tls plugin block, got:\n%s", strContent)
	}
	if !strings.Contains(strContent, "reverse_proxy localhost:8081") {
		t.Errorf("expected reverse proxy to 8081, got:\n%s", strContent)
	}
	if strings.Contains(strContent, "https_port") {
		t.Errorf("port 443 should not specify https_port directive in global block, got:\n%s", strContent)
	}

	// Test 2: Custom port 8443 without token
	path2, err2 := mgr.GenerateCaddyfile("porto-alegre", 8081, 8443, "")
	if err2 != nil {
		t.Fatalf("expected generation to succeed on 8443, got %v", err2)
	}

	content2, _ := os.ReadFile(path2)
	str2 := string(content2)
	if !strings.Contains(str2, "https_port 8443") {
		t.Errorf("expected https_port 8443 in global block, got:\n%s", str2)
	}
	if !strings.Contains(str2, "porto-alegre.duckdns.org:8443 {") {
		t.Errorf("expected site block with :8443, got:\n%s", str2)
	}
	if strings.Contains(str2, "dns duckdns") {
		t.Errorf("empty token should not generate dns duckdns block, got:\n%s", str2)
	}
}

func TestCaddyManagerPublicURL(t *testing.T) {
	mgr := NewCaddyManager("dummy-bin", "dummy-caddyfile", nil)
	mgr.subdomain = "saopaulo"
	mgr.activePort = 443
	if mgr.PublicURL() != "https://saopaulo.duckdns.org" {
		t.Errorf("expected https://saopaulo.duckdns.org, got %s", mgr.PublicURL())
	}

	mgr.activePort = 8443
	if mgr.PublicURL() != "https://saopaulo.duckdns.org:8443" {
		t.Errorf("expected https://saopaulo.duckdns.org:8443, got %s", mgr.PublicURL())
	}
}
