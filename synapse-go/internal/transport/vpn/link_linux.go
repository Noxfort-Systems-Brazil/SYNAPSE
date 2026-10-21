// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

package vpn

import (
	"fmt"
	"os/exec"
	"strings"
)

// LinuxLinkManager configures the WireGuard network interface using the Linux 'ip' utility.
type LinuxLinkManager struct{}

// NewLinuxLinkManager creates a new LinuxLinkManager instance.
func NewLinuxLinkManager() *LinuxLinkManager {
	return &LinuxLinkManager{}
}

// EnsureInterface checks if the WireGuard interface exists; if missing, creates it, assigns IP, and brings it UP.
func (l *LinuxLinkManager) EnsureInterface(name, serverIP string) error {
	// 1. Check if interface already exists
	checkCmd := exec.Command("ip", "link", "show", name)
	if err := checkCmd.Run(); err == nil {
		// Interface exists; ensure IP is bound and device is UP
		_ = exec.Command("ip", "addr", "add", serverIP, "dev", name).Run()
		_ = exec.Command("ip", "link", "set", "up", "dev", name).Run()
		return nil
	}

	// 2. Create WireGuard link interface
	addCmd := exec.Command("ip", "link", "add", "dev", name, "type", "wireguard")
	if out, err := addCmd.CombinedOutput(); err != nil {
		return fmt.Errorf("ip link add failed (%s): %w", strings.TrimSpace(string(out)), err)
	}

	// 3. Assign server IP and CIDR mask
	addrCmd := exec.Command("ip", "addr", "add", serverIP, "dev", name)
	if out, err := addrCmd.CombinedOutput(); err != nil {
		return fmt.Errorf("ip addr add failed (%s): %w", strings.TrimSpace(string(out)), err)
	}

	// 4. Set interface state to UP
	upCmd := exec.Command("ip", "link", "set", "up", "dev", name)
	if out, err := upCmd.CombinedOutput(); err != nil {
		return fmt.Errorf("ip link set up failed (%s): %w", strings.TrimSpace(string(out)), err)
	}

	return nil
}

// DeleteInterface tears down and deletes the specified network link interface.
func (l *LinuxLinkManager) DeleteInterface(name string) error {
	delCmd := exec.Command("ip", "link", "del", "dev", name)
	if out, err := delCmd.CombinedOutput(); err != nil {
		return fmt.Errorf("ip link del failed (%s): %w", strings.TrimSpace(string(out)), err)
	}
	return nil
}
