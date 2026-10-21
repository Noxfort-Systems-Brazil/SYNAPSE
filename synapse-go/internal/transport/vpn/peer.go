// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

package vpn

import (
	"fmt"
	"strings"
	"time"

	"golang.zx2c4.com/wireguard/wgctrl/wgtypes"
)

// Peer represents an authorized edge sensor or camera node in the WireGuard VPN.
type Peer struct {
	ID            string    `json:"id"`
	PublicKey     string    `json:"public_key"`
	PrivateKey    string    `json:"private_key,omitempty"` // Retained for client configuration generation
	IP            string    `json:"ip"`                     // e.g. "10.10.0.2"
	CreatedAt     time.Time `json:"created_at"`
	LastHandshake time.Time `json:"last_handshake,omitempty"`
}

// GeneratePeerCredentials generates a new Curve25519 key pair for a sensor node.
func GeneratePeerCredentials(id string, ip string) (*Peer, error) {
	privKey, err := wgtypes.GeneratePrivateKey()
	if err != nil {
		return nil, fmt.Errorf("failed to generate private key: %w", err)
	}

	pubKey := privKey.PublicKey()

	return &Peer{
		ID:         id,
		PublicKey:  pubKey.String(),
		PrivateKey: privKey.String(),
		IP:         ip,
		CreatedAt:  time.Now().UTC(),
	}, nil
}

// GenerateClientConfig generates a ready-to-use WireGuard configuration file (.conf)
// for the field camera, radar station, or industrial IoT router.
func (p *Peer) GenerateClientConfig(serverPubKey, serverEndpoint, serverVPNIP string, keepaliveSec int) string {
	if keepaliveSec <= 0 {
		keepaliveSec = 25
	}

	// Clean server VPN IP (strip CIDR mask if present for AllowedIPs)
	cleanServerIP := strings.Split(serverVPNIP, "/")[0]

	return fmt.Sprintf(`# SYNAPSE Edge Sensor WireGuard VPN Profile
# Sensor ID: %s
# Generated: %s

[Interface]
PrivateKey = %s
Address = %s/24

[Peer]
PublicKey = %s
Endpoint = %s
AllowedIPs = %s/32
PersistentKeepalive = %d
`, p.ID, p.CreatedAt.Format(time.RFC3339), p.PrivateKey, p.IP, serverPubKey, serverEndpoint, cleanServerIP, keepaliveSec)
}
