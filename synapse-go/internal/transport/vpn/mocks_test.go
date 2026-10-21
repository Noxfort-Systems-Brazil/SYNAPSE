// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

package vpn

import (
	"time"

	"golang.zx2c4.com/wireguard/wgctrl/wgtypes"
)

// MockLinkManager simulates OS network interface interactions.
type MockLinkManager struct {
	ensuredInterface string
	ensuredIP        string
	ensureCalls      int
	deleteCalls      int
}

func (m *MockLinkManager) EnsureInterface(name, serverIP string) error {
	m.ensuredInterface = name
	m.ensuredIP = serverIP
	m.ensureCalls++
	return nil
}

func (m *MockLinkManager) DeleteInterface(name string) error {
	m.deleteCalls++
	return nil
}

// MockDeviceController simulates WireGuard interactions in-memory.
type MockDeviceController struct {
	syncedName     string
	syncedPrivKey  wgtypes.Key
	syncedPort     int
	syncedPeers    []*Peer
	addedPeers     []*Peer
	removedKeys    []string
	handshakeCalls int
	closed         bool
}

func (m *MockDeviceController) SyncServer(name string, privKey wgtypes.Key, port int, peers []*Peer) error {
	m.syncedName = name
	m.syncedPrivKey = privKey
	m.syncedPort = port
	m.syncedPeers = peers
	return nil
}

func (m *MockDeviceController) AddPeer(name string, peer *Peer) error {
	m.addedPeers = append(m.addedPeers, peer)
	return nil
}

func (m *MockDeviceController) RemovePeer(name string, publicKey string) error {
	m.removedKeys = append(m.removedKeys, publicKey)
	return nil
}

func (m *MockDeviceController) SyncHandshakes(name string, peers []*Peer) error {
	m.handshakeCalls++
	for _, p := range peers {
		if p != nil {
			p.LastHandshake = time.Now().Add(-5 * time.Second)
		}
	}
	return nil
}

func (m *MockDeviceController) Close() error {
	m.closed = true
	return nil
}
