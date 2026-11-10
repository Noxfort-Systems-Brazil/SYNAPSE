// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

package vpn

import (
	"path/filepath"
	"strings"
	"testing"
)

func TestManager_PureSOLID_WithMocks(t *testing.T) {
	tmpDir := t.TempDir()
	storagePath := filepath.Join(tmpDir, "vpn_state_mock.json")

	storage, err := NewStorage(storagePath)
	if err != nil {
		t.Fatalf("failed to create storage: %v", err)
	}

	mockLink := &MockLinkManager{}
	mockDev := &MockDeviceController{}
	allocator := NewSequentialIPAllocator()

	cfg := Config{
		InterfaceName: "wg_mock0",
		Port:          51820,
		ServerIP:      "10.10.0.1/24",
		Endpoint:      "vpn.mock.noxfort.com:51820",
		StoragePath:   storagePath,
	}

	// 1. Dependency Inversion: Inject all mocks
	mgr, err := NewManager(cfg, storage, mockLink, mockDev, allocator)
	if err != nil {
		t.Fatalf("NewManager error: %v", err)
	}

	// 2. Verify IVPNManager conformance
	var _ IVPNManager = mgr

	// 3. Start facade
	if err := mgr.Start(); err != nil {
		t.Fatalf("Start error: %v", err)
	}

	if !mgr.IsActive() {
		t.Errorf("expected manager to be active")
	}
	if mockLink.ensureCalls != 1 {
		t.Errorf("expected 1 EnsureInterface call, got %d", mockLink.ensureCalls)
	}
	if mockDev.syncedPort != 51820 {
		t.Errorf("expected synced port 51820, got %d", mockDev.syncedPort)
	}
	if len(mgr.GetServerPublicKey()) != 44 {
		t.Errorf("expected 44-character server public key")
	}

	// 4. Register Peer
	peer, clientConf, err := mgr.RegisterPeer("sensor_mock_01")
	if err != nil {
		t.Fatalf("RegisterPeer error: %v", err)
	}
	if peer.ID != "sensor_mock_01" {
		t.Errorf("expected peer ID 'sensor_mock_01', got '%s'", peer.ID)
	}
	if peer.IP != "10.10.0.2" {
		t.Errorf("expected peer IP '10.10.0.2', got '%s'", peer.IP)
	}
	if !strings.Contains(clientConf, "Endpoint = vpn.mock.noxfort.com:51820") {
		t.Errorf("expected endpoint in client config")
	}

	// 5. List Peers
	peers := mgr.ListPeers()
	if len(peers) != 1 {
		t.Errorf("expected 1 peer, got %d", len(peers))
	}

	// 6. Remove Peer
	if err := mgr.RemovePeer("sensor_mock_01"); err != nil {
		t.Fatalf("RemovePeer error: %v", err)
	}
	if len(mgr.ListPeers()) != 0 {
		t.Errorf("expected 0 peers after removal")
	}

	// 7. Close facade
	if err := mgr.Close(); err != nil {
		t.Fatalf("Close error: %v", err)
	}
	if !mockDev.closed {
		t.Errorf("expected mock device to be closed")
	}
}

func TestManager_DefaultFactory(t *testing.T) {
	tmpDir := t.TempDir()
	storagePath := filepath.Join(tmpDir, "vpn_state_default.json")

	mgr, err := NewDefaultManager(Config{
		InterfaceName: "wg_default_test",
		Port:          51822,
		ServerIP:      "10.30.0.1/24",
		Endpoint:      "vpn.noxfort.com:51822",
		StoragePath:   storagePath,
	})
	if err != nil {
		t.Fatalf("NewDefaultManager error: %v", err)
	}
	defer mgr.Close()

	if err := mgr.Start(); err != nil {
		t.Fatalf("Start error: %v", err)
	}

	// Register peer in graceful degradation mode (works even without root)
	peer, clientConf, err := mgr.RegisterPeer("cam_def_01")
	if err != nil {
		t.Fatalf("RegisterPeer error: %v", err)
	}
	if peer.IP != "10.30.0.2" {
		t.Errorf("expected peer IP '10.30.0.2', got '%s'", peer.IP)
	}
	if !strings.Contains(clientConf, "Address = 10.30.0.2/24") {
		t.Errorf("expected Address in config")
	}
}
