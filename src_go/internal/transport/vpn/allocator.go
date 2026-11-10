// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

package vpn

import (
	"fmt"
	"net"
	"strconv"
	"strings"
	"sync"
)

// SequentialIPAllocator allocates IP addresses sequentially within a base subnet.
type SequentialIPAllocator struct {
	mu sync.Mutex
}

// NewSequentialIPAllocator creates a new sequential IP allocator.
func NewSequentialIPAllocator() *SequentialIPAllocator {
	return &SequentialIPAllocator{}
}

// ExtractBaseSubnet extracts the /24 prefix from a CIDR notation or IP address.
// Example: "10.10.0.1/24" -> "10.10.0", "192.168.15.1" -> "192.168.15".
func (a *SequentialIPAllocator) ExtractBaseSubnet(serverCIDR string) string {
	clean := strings.TrimSpace(serverCIDR)
	if idx := strings.Index(clean, "/"); idx != -1 {
		clean = clean[:idx]
	}

	ip := net.ParseIP(clean)
	if ip == nil {
		// Fallback to manual split if not standard IPv4
		parts := strings.Split(clean, ".")
		if len(parts) >= 3 {
			return fmt.Sprintf("%s.%s.%s", parts[0], parts[1], parts[2])
		}
		return "10.10.0"
	}

	ipv4 := ip.To4()
	if ipv4 == nil {
		return "10.10.0"
	}

	return fmt.Sprintf("%d.%d.%d", ipv4[0], ipv4[1], ipv4[2])
}

// AllocateIP discovers the next available IPv4 address in the given base subnet
// by scanning existing peers and picking the next sequential host index (starting at 2).
func (a *SequentialIPAllocator) AllocateIP(baseSubnet string, existing []*Peer) string {
	a.mu.Lock()
	defer a.mu.Unlock()

	highest := 1 // Host .1 is reserved for the VPN Server Gateway

	prefix := baseSubnet + "."
	for _, p := range existing {
		if p == nil {
			continue
		}
		if strings.HasPrefix(p.IP, prefix) {
			lastPart := strings.TrimPrefix(p.IP, prefix)
			if idx, err := strconv.Atoi(lastPart); err == nil {
				if idx > highest {
					highest = idx
				}
			}
		}
	}

	nextHost := highest + 1
	if nextHost > 254 {
		// Wrapped or exhausted /24 subnet, start scan for holes
		used := make(map[int]bool)
		for _, p := range existing {
			if p != nil && strings.HasPrefix(p.IP, prefix) {
				lastPart := strings.TrimPrefix(p.IP, prefix)
				if idx, err := strconv.Atoi(lastPart); err == nil {
					used[idx] = true
				}
			}
		}
		for candidate := 2; candidate <= 254; candidate++ {
			if !used[candidate] {
				return fmt.Sprintf("%s.%d", baseSubnet, candidate)
			}
		}
	}

	return fmt.Sprintf("%s.%d", baseSubnet, nextHost)
}
