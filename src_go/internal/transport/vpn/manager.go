// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

package vpn

import (
	"fmt"
	"log"
	"sync"

	"golang.zx2c4.com/wireguard/wgctrl/wgtypes"
)

// Manager is the pure facade orchestrator managing WireGuard VPN lifecycle and peers.
type Manager struct {
	cfg       Config
	repo      PeerRepository
	link      LinkManager
	device    DeviceController
	allocator IPAllocator

	serverPrivKey wgtypes.Key
	serverPubKey  wgtypes.Key
	isActive      bool
	mu            sync.RWMutex
}

// NewManager creates a WireGuard VPN Manager using explicit Dependency Injection (DIP).
func NewManager(cfg Config, repo PeerRepository, link LinkManager, device DeviceController, allocator IPAllocator) (*Manager, error) {
	cfg.Normalize()
	if repo == nil {
		return nil, fmt.Errorf("peer repository cannot be nil")
	}
	if allocator == nil {
		allocator = NewSequentialIPAllocator()
	}
	return &Manager{
		cfg:       cfg,
		repo:      repo,
		link:      link,
		device:    device,
		allocator: allocator,
	}, nil
}

// Start initializes server cryptographic keys and configures the WireGuard interface and device.
func (m *Manager) Start() error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if err := m.ensureServerKeys(); err != nil {
		return err
	}
	log.Printf("🔑 [synapse-go-vpn] Server Public Key: %s", m.serverPubKey.String())

	if m.link != nil {
		if err := m.link.EnsureInterface(m.cfg.InterfaceName, m.cfg.ServerIP); err != nil {
			log.Printf("⚠️ [synapse-go-vpn] Kernel interface setup notice: %v", err)
			log.Printf("ℹ️ [synapse-go-vpn] Peer key generation and credentials management remain 100%% active.")
			return nil
		}
	}

	if m.device != nil {
		if err := m.device.SyncServer(m.cfg.InterfaceName, m.serverPrivKey, m.cfg.Port, m.repo.ListPeers()); err != nil {
			log.Printf("⚠️ [synapse-go-vpn] SyncServer error: %v", err)
			return nil
		}
		m.isActive = true
		log.Printf("🛡️ [synapse-go-vpn] WireGuard VPN Online on %s (%s, UDP %d).", m.cfg.InterfaceName, m.cfg.ServerIP, m.cfg.Port)
	}

	return nil
}

// RegisterPeer generates a new sensor peer, registers it with WireGuard, and produces the client config.
func (m *Manager) RegisterPeer(sourceID string) (*Peer, string, error) {
	m.mu.Lock()
	defer m.mu.Unlock()

	if existing, found := m.repo.GetPeer(sourceID); found {
		return existing, existing.GenerateClientConfig(m.serverPubKey.String(), m.cfg.Endpoint, m.cfg.ServerIP, 25), nil
	}

	baseSubnet := m.allocator.ExtractBaseSubnet(m.cfg.ServerIP)
	clientIP := m.allocator.AllocateIP(baseSubnet, m.repo.ListPeers())

	peer, err := GeneratePeerCredentials(sourceID, clientIP)
	if err != nil {
		return nil, "", fmt.Errorf("failed to generate peer credentials: %w", err)
	}

	if m.isActive && m.device != nil {
		if err := m.device.AddPeer(m.cfg.InterfaceName, peer); err != nil {
			log.Printf("⚠️ [synapse-go-vpn] Could not add peer to device: %v", err)
		}
	}

	if err := m.repo.AddPeer(peer); err != nil {
		log.Printf("⚠️ [synapse-go-vpn] Could not persist peer: %v", err)
	}

	clientConf := peer.GenerateClientConfig(m.serverPubKey.String(), m.cfg.Endpoint, m.cfg.ServerIP, 25)
	log.Printf("📡 [synapse-go-vpn] Registered sensor peer '%s' -> IP %s", sourceID, clientIP)
	return peer, clientConf, nil
}

// RemovePeer unregisters a peer from the WireGuard device and repository.
func (m *Manager) RemovePeer(sourceID string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	peer, err := m.repo.RemovePeer(sourceID)
	if err != nil || peer == nil {
		return err
	}

	if m.isActive && m.device != nil {
		_ = m.device.RemovePeer(m.cfg.InterfaceName, peer.PublicKey)
	}

	log.Printf("🗑️ [synapse-go-vpn] Unregistered sensor peer '%s' (%s)", sourceID, peer.IP)
	return nil
}

// ListPeers retrieves all registered peers, merging live telemetry handshakes if the device is active.
func (m *Manager) ListPeers() []*Peer {
	m.mu.RLock()
	peers := m.repo.ListPeers()
	m.mu.RUnlock()

	if m.isActive && m.device != nil {
		_ = m.device.SyncHandshakes(m.cfg.InterfaceName, peers)
	}
	return peers
}

// GetServerPublicKey returns the base64 Curve25519 public key of the VPN server.
func (m *Manager) GetServerPublicKey() string {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.serverPubKey.String()
}

// IsActive returns whether the WireGuard kernel interface is active.
func (m *Manager) IsActive() bool {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.isActive
}

// Close gracefully shuts down the device and releases resources.
func (m *Manager) Close() error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.device != nil {
		_ = m.device.Close()
	}
	m.isActive = false
	return nil
}

// ensureServerKeys loads persisted keys or generates a new Curve25519 server keypair.
func (m *Manager) ensureServerKeys() error {
	storedPriv, storedPub := m.repo.GetServerKeys()
	if storedPriv != "" && storedPub != "" {
		if privKey, err := wgtypes.ParseKey(storedPriv); err == nil {
			m.serverPrivKey = privKey
			m.serverPubKey = privKey.PublicKey()
			return nil
		}
	}

	privKey, err := wgtypes.GeneratePrivateKey()
	if err != nil {
		return fmt.Errorf("failed to generate WireGuard server private key: %w", err)
	}
	m.serverPrivKey = privKey
	m.serverPubKey = privKey.PublicKey()

	_ = m.repo.SetServerKeys(privKey.String(), m.serverPubKey.String())
	return nil
}
