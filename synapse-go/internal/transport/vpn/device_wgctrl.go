// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

package vpn

import (
	"fmt"
	"net"
	"sync"
	"time"

	"golang.zx2c4.com/wireguard/wgctrl"
	"golang.zx2c4.com/wireguard/wgctrl/wgtypes"
)

// WgctrlDeviceController interacts with the kernel WireGuard device via Netlink using wgctrl.
type WgctrlDeviceController struct {
	client *wgctrl.Client
	mu     sync.Mutex
}

// NewWgctrlDeviceController creates a new WgctrlDeviceController connected to Netlink.
func NewWgctrlDeviceController() (*WgctrlDeviceController, error) {
	client, err := wgctrl.New()
	if err != nil {
		return nil, fmt.Errorf("failed to connect to wgctrl netlink: %w", err)
	}
	return &WgctrlDeviceController{client: client}, nil
}

// SyncServer synchronizes the server private key, port, and peer table into the WireGuard kernel interface.
func (w *WgctrlDeviceController) SyncServer(name string, privKey wgtypes.Key, port int, peers []*Peer) error {
	w.mu.Lock()
	defer w.mu.Unlock()

	if w.client == nil {
		return fmt.Errorf("wgctrl client is closed")
	}

	peerConfigs := make([]wgtypes.PeerConfig, 0, len(peers))
	for _, p := range peers {
		if p == nil {
			continue
		}
		pubKey, err := wgtypes.ParseKey(p.PublicKey)
		if err != nil {
			continue
		}
		ip := net.ParseIP(p.IP)
		if ip == nil {
			continue
		}
		peerConfigs = append(peerConfigs, wgtypes.PeerConfig{
			PublicKey: pubKey,
			AllowedIPs: []net.IPNet{
				{IP: ip, Mask: net.CIDRMask(32, 32)},
			},
			ReplaceAllowedIPs: true,
		})
	}

	devConfig := wgtypes.Config{
		PrivateKey:   &privKey,
		ListenPort:   &port,
		Peers:        peerConfigs,
		ReplacePeers: true,
	}

	return w.client.ConfigureDevice(name, devConfig)
}

// AddPeer adds or updates an authorized peer in the kernel WireGuard interface.
func (w *WgctrlDeviceController) AddPeer(name string, peer *Peer) error {
	w.mu.Lock()
	defer w.mu.Unlock()

	if w.client == nil || peer == nil {
		return fmt.Errorf("wgctrl client is closed or peer is nil")
	}

	pubKey, err := wgtypes.ParseKey(peer.PublicKey)
	if err != nil {
		return fmt.Errorf("invalid peer public key: %w", err)
	}

	ip := net.ParseIP(peer.IP)
	if ip == nil {
		return fmt.Errorf("invalid peer IP '%s'", peer.IP)
	}

	peerCfg := wgtypes.PeerConfig{
		PublicKey: pubKey,
		AllowedIPs: []net.IPNet{
			{IP: ip, Mask: net.CIDRMask(32, 32)},
		},
		ReplaceAllowedIPs: true,
	}

	return w.client.ConfigureDevice(name, wgtypes.Config{
		Peers: []wgtypes.PeerConfig{peerCfg},
	})
}

// RemovePeer removes an authorized peer from the kernel WireGuard interface.
func (w *WgctrlDeviceController) RemovePeer(name string, publicKey string) error {
	w.mu.Lock()
	defer w.mu.Unlock()

	if w.client == nil {
		return fmt.Errorf("wgctrl client is closed")
	}

	pubKey, err := wgtypes.ParseKey(publicKey)
	if err != nil {
		return fmt.Errorf("invalid peer public key: %w", err)
	}

	return w.client.ConfigureDevice(name, wgtypes.Config{
		Peers: []wgtypes.PeerConfig{
			{
				PublicKey: pubKey,
				Remove:    true,
			},
		},
	})
}

// SyncHandshakes polls the kernel device and enriches the supplied peers with live handshake timestamps.
func (w *WgctrlDeviceController) SyncHandshakes(name string, peers []*Peer) error {
	w.mu.Lock()
	defer w.mu.Unlock()

	if w.client == nil {
		return fmt.Errorf("wgctrl client is closed")
	}

	dev, err := w.client.Device(name)
	if err != nil {
		return err
	}

	liveMap := make(map[string]time.Time, len(dev.Peers))
	for _, p := range dev.Peers {
		liveMap[p.PublicKey.String()] = p.LastHandshakeTime
	}

	for _, p := range peers {
		if p == nil {
			continue
		}
		if t, ok := liveMap[p.PublicKey]; ok && !t.IsZero() {
			p.LastHandshake = t
		}
	}

	return nil
}

// Close gracefully terminates the Netlink client connection.
func (w *WgctrlDeviceController) Close() error {
	w.mu.Lock()
	defer w.mu.Unlock()

	if w.client != nil {
		err := w.client.Close()
		w.client = nil
		return err
	}
	return nil
}
