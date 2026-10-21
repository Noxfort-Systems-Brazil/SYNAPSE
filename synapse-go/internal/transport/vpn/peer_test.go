// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

package vpn

import (
	"path/filepath"
	"strings"
	"testing"
)

func TestGeneratePeerCredentials(t *testing.T) {
	peer, err := GeneratePeerCredentials("cam_north", "10.10.0.2")
	if err != nil {
		t.Fatalf("GeneratePeerCredentials error: %v", err)
	}

	if peer.ID != "cam_north" {
		t.Errorf("expected ID 'cam_north', got '%s'", peer.ID)
	}
	if peer.IP != "10.10.0.2" {
		t.Errorf("expected IP '10.10.0.2', got '%s'", peer.IP)
	}
	if len(peer.PublicKey) != 44 { // Standard 32-byte base64 key has 44 chars
		t.Errorf("expected 44-char base64 public key, got '%s' (len %d)", peer.PublicKey, len(peer.PublicKey))
	}
	if len(peer.PrivateKey) != 44 {
		t.Errorf("expected 44-char base64 private key, got '%s' (len %d)", peer.PrivateKey, len(peer.PrivateKey))
	}
}

func TestGenerateClientConfig(t *testing.T) {
	peer, err := GeneratePeerCredentials("radar_south", "10.10.0.5")
	if err != nil {
		t.Fatalf("GeneratePeerCredentials error: %v", err)
	}

	serverPub := "J98nfk2hK3sL1m4N5p6Q7r8S9t0U1v2W3x4Y5z6A7b8="
	serverEndpoint := "200.150.10.20:51820"
	serverVPNIP := "10.10.0.1/24"

	conf := peer.GenerateClientConfig(serverPub, serverEndpoint, serverVPNIP, 25)

	if !strings.Contains(conf, "[Interface]") {
		t.Errorf("expected '[Interface]' section in config")
	}
	if !strings.Contains(conf, "Address = 10.10.0.5/24") {
		t.Errorf("expected 'Address = 10.10.0.5/24' in config")
	}
	if !strings.Contains(conf, "[Peer]") {
		t.Errorf("expected '[Peer]' section in config")
	}
	if !strings.Contains(conf, "Endpoint = 200.150.10.20:51820") {
		t.Errorf("expected server endpoint in config")
	}
	if !strings.Contains(conf, "AllowedIPs = 10.10.0.1/32") {
		t.Errorf("expected 'AllowedIPs = 10.10.0.1/32' in config")
	}
	if !strings.Contains(conf, "PersistentKeepalive = 25") {
		t.Errorf("expected 'PersistentKeepalive = 25' in config")
	}
}

func TestSequentialIPAllocator(t *testing.T) {
	alloc := NewSequentialIPAllocator()

	// 1. Subnet extraction
	if sub := alloc.ExtractBaseSubnet("10.10.0.1/24"); sub != "10.10.0" {
		t.Errorf("expected '10.10.0', got '%s'", sub)
	}
	if sub := alloc.ExtractBaseSubnet("192.168.15.1"); sub != "192.168.15" {
		t.Errorf("expected '192.168.15', got '%s'", sub)
	}

	// 2. Allocation without existing peers
	ip1 := alloc.AllocateIP("10.10.0", nil)
	if ip1 != "10.10.0.2" {
		t.Errorf("expected initial client IP '10.10.0.2', got '%s'", ip1)
	}

	// 3. Allocation with existing peers
	existing := []*Peer{
		{ID: "p1", IP: "10.10.0.2"},
		{ID: "p2", IP: "10.10.0.3"},
	}
	ip2 := alloc.AllocateIP("10.10.0", existing)
	if ip2 != "10.10.0.4" {
		t.Errorf("expected next client IP '10.10.0.4', got '%s'", ip2)
	}
}

func TestStorage_PersistenceAndIPSequencing(t *testing.T) {
	tmpDir := t.TempDir()
	storagePath := filepath.Join(tmpDir, "vpn_test.json")

	storage, err := NewStorage(storagePath)
	if err != nil {
		t.Fatalf("NewStorage error: %v", err)
	}

	// 1. Check IP sequence
	ip1 := storage.NextIP("10.10.0")
	ip2 := storage.NextIP("10.10.0")
	if ip1 != "10.10.0.2" {
		t.Errorf("expected first client IP 10.10.0.2, got %s", ip1)
	}
	if ip2 != "10.10.0.3" {
		t.Errorf("expected second client IP 10.10.0.3, got %s", ip2)
	}

	// 2. Add Peer
	peer := &Peer{
		ID:        "cam_01",
		PublicKey: "mock_pub_key",
		IP:        ip1,
	}
	if err := storage.AddPeer(peer); err != nil {
		t.Fatalf("AddPeer error: %v", err)
	}

	// 3. Re-open storage to verify persistence
	storage2, err := NewStorage(storagePath)
	if err != nil {
		t.Fatalf("Re-opening storage error: %v", err)
	}

	p, found := storage2.GetPeer("cam_01")
	if !found || p.IP != "10.10.0.2" {
		t.Errorf("expected restored peer cam_01 with IP 10.10.0.2")
	}

	// Next IP should continue from 4
	ip3 := storage2.NextIP("10.10.0")
	if ip3 != "10.10.0.4" {
		t.Errorf("expected restored next IP 10.10.0.4, got %s", ip3)
	}
}
