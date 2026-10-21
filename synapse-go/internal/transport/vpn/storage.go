// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

package vpn

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
)

// State represents the persistent WireGuard configuration and peer registry.
type State struct {
	ServerPrivateKey string           `json:"server_private_key"`
	ServerPublicKey  string           `json:"server_public_key"`
	NextIPIndex      int              `json:"next_ip_index"`
	Peers            map[string]*Peer `json:"peers"` // Keyed by Peer ID
}

// Storage handles atomic persistence of VPN state to disk.
type Storage struct {
	filePath string
	mu       sync.RWMutex
	state    *State
}

// NewStorage initializes state storage from the given file path.
func NewStorage(filePath string) (*Storage, error) {
	s := &Storage{
		filePath: filePath,
		state: &State{
			NextIPIndex: 2, // 10.10.0.1 is reserved for the Synapse server
			Peers:       make(map[string]*Peer),
		},
	}

	if err := s.load(); err != nil && !os.IsNotExist(err) {
		return nil, fmt.Errorf("failed to load VPN state: %w", err)
	}

	return s, nil
}

func (s *Storage) load() error {
	s.mu.Lock()
	defer s.mu.Unlock()

	data, err := os.ReadFile(s.filePath)
	if err != nil {
		return err
	}

	var state State
	if err := json.Unmarshal(data, &state); err != nil {
		return fmt.Errorf("malformed VPN state JSON: %w", err)
	}

	if state.Peers == nil {
		state.Peers = make(map[string]*Peer)
	}
	if state.NextIPIndex < 2 {
		state.NextIPIndex = 2
	}

	s.state = &state
	return nil
}

// Save flushes the current VPN state to disk atomically.
func (s *Storage) Save() error {
	s.mu.RLock()
	defer s.mu.RUnlock()

	data, err := json.MarshalIndent(s.state, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to encode VPN state: %w", err)
	}

	dir := filepath.Dir(s.filePath)
	if err := os.MkdirAll(dir, 0750); err != nil {
		return fmt.Errorf("failed to create directory %s: %w", dir, err)
	}

	tmpFile := s.filePath + ".tmp"
	if err := os.WriteFile(tmpFile, data, 0600); err != nil {
		return fmt.Errorf("failed to write temporary state file: %w", err)
	}

	if err := os.Rename(tmpFile, s.filePath); err != nil {
		return fmt.Errorf("failed to commit state file: %w", err)
	}

	return nil
}

// GetServerKeys returns the stored server key pair, if available.
func (s *Storage) GetServerKeys() (privateKey, publicKey string) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.state.ServerPrivateKey, s.state.ServerPublicKey
}

// SetServerKeys records the server key pair.
func (s *Storage) SetServerKeys(privateKey, publicKey string) error {
	s.mu.Lock()
	s.state.ServerPrivateKey = privateKey
	s.state.ServerPublicKey = publicKey
	s.mu.Unlock()
	return s.Save()
}

// NextIP computes and reserves the next available client IP address.
func (s *Storage) NextIP(baseSubnet string) string {
	s.mu.Lock()
	defer s.mu.Unlock()

	ip := fmt.Sprintf("%s.%d", baseSubnet, s.state.NextIPIndex)
	s.state.NextIPIndex++
	return ip
}

// AddPeer registers or updates a peer in storage.
func (s *Storage) AddPeer(peer *Peer) error {
	s.mu.Lock()
	s.state.Peers[peer.ID] = peer
	s.mu.Unlock()
	return s.Save()
}

// RemovePeer removes a peer by ID.
func (s *Storage) RemovePeer(peerID string) (*Peer, error) {
	s.mu.Lock()
	peer, exists := s.state.Peers[peerID]
	if exists {
		delete(s.state.Peers, peerID)
	}
	s.mu.Unlock()

	if exists {
		_ = s.Save()
	}
	return peer, nil
}

// GetPeer retrieves a peer by ID.
func (s *Storage) GetPeer(peerID string) (*Peer, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	p, ok := s.state.Peers[peerID]
	return p, ok
}

// ListPeers returns a slice of all registered peers.
func (s *Storage) ListPeers() []*Peer {
	s.mu.RLock()
	defer s.mu.RUnlock()

	result := make([]*Peer, 0, len(s.state.Peers))
	for _, p := range s.state.Peers {
		result = append(result, p)
	}
	return result
}
