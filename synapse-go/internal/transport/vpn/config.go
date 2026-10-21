// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

package vpn

import (
	"fmt"
	"log"
)

// Config provides initialization parameters for the WireGuard VPN subsystem.
type Config struct {
	InterfaceName string
	Port          int
	ServerIP      string // e.g. "10.10.0.1/24"
	Endpoint      string // e.g. "200.150.x.x:51820" or "vpn.domain.com:51820"
	StoragePath   string
}

// Normalize applies default values to unpopulated configuration fields.
func (c *Config) Normalize() {
	if c.InterfaceName == "" {
		c.InterfaceName = "wg0"
	}
	if c.Port <= 0 {
		c.Port = 51820
	}
	if c.ServerIP == "" {
		c.ServerIP = "10.10.0.1/24"
	}
	if c.Endpoint == "" {
		c.Endpoint = fmt.Sprintf("127.0.0.1:%d", c.Port)
	}
	if c.StoragePath == "" {
		c.StoragePath = "config/vpn_state.json"
	}
}

// NewDefaultManager creates a WireGuard VPN Manager wired with default Linux production components.
func NewDefaultManager(cfg Config) (*Manager, error) {
	cfg.Normalize()

	storage, err := NewStorage(cfg.StoragePath)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize VPN storage: %w", err)
	}

	link := NewLinuxLinkManager()

	var device DeviceController
	if devCtrl, err := NewWgctrlDeviceController(); err == nil {
		device = devCtrl
	} else {
		log.Printf("ℹ️ [synapse-go-vpn] Wgctrl device controller not available: %v", err)
	}

	allocator := NewSequentialIPAllocator()

	return NewManager(cfg, storage, link, device, allocator)
}
