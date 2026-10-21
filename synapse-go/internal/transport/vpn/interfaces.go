// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

package vpn

import (
	"golang.zx2c4.com/wireguard/wgctrl/wgtypes"
)

// IVPNManager defines the public facade interface for WireGuard VPN orchestration.
type IVPNManager interface {
	Start() error
	RegisterPeer(sourceID string) (*Peer, string, error)
	RemovePeer(sourceID string) error
	ListPeers() []*Peer
	GetServerPublicKey() string
	IsActive() bool
	Close() error
}

// LinkManager abstracts OS network interface configuration (e.g. Linux ip link / netlink).
type LinkManager interface {
	EnsureInterface(name, serverIP string) error
	DeleteInterface(name string) error
}

// DeviceController abstracts the WireGuard driver/netlink controller in high-level domain terms.
type DeviceController interface {
	SyncServer(name string, privKey wgtypes.Key, port int, peers []*Peer) error
	AddPeer(name string, peer *Peer) error
	RemovePeer(name string, publicKey string) error
	SyncHandshakes(name string, peers []*Peer) error
	Close() error
}

// PeerRepository abstracts persistence of server cryptographic keys and peer configurations.
type PeerRepository interface {
	GetServerKeys() (privKey, pubKey string)
	SetServerKeys(privKey, pubKey string) error
	AddPeer(peer *Peer) error
	RemovePeer(sourceID string) (*Peer, error)
	GetPeer(sourceID string) (*Peer, bool)
	ListPeers() []*Peer
	NextIP(baseSubnet string) string
}

// IPAllocator abstracts IP address subnet resolution and dynamic allocation.
type IPAllocator interface {
	ExtractBaseSubnet(serverCIDR string) string
	AllocateIP(baseSubnet string, existing []*Peer) string
}
