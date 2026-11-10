// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

package tunnel

import (
	"net"
	"strings"
)

// CleanDuckDNSToken strips whitespace and quotes from DuckDNS tokens.
func CleanDuckDNSToken(raw string) string {
	raw = strings.TrimSpace(raw)
	raw = strings.Trim(raw, `"'`)
	return strings.TrimSpace(raw)
}

// CleanDuckDNSDomain extracts the subdomain name from a user string.
// E.g. "prefeitura-synapse.duckdns.org" -> "prefeitura-synapse", "https://prefeitura-synapse" -> "prefeitura-synapse".
func CleanDuckDNSDomain(raw string) string {
	raw = strings.TrimSpace(raw)
	raw = strings.TrimPrefix(raw, "https://")
	raw = strings.TrimPrefix(raw, "http://")
	raw = strings.TrimSuffix(raw, "/")
	raw = strings.TrimSuffix(raw, ".duckdns.org")
	return strings.TrimSpace(raw)
}

// DetectGlobalIPv6 inspects network interfaces and returns the first public global unicast IPv6.
func DetectGlobalIPv6() string {
	addrs, err := net.InterfaceAddrs()
	if err != nil {
		return ""
	}

	for _, addr := range addrs {
		ipNet, ok := addr.(*net.IPNet)
		if !ok || ipNet.IP == nil {
			continue
		}

		ip := ipNet.IP
		// Check if it is an IPv6 address and not an IPv4-mapped address
		if ip.To4() == nil && ip.To16() != nil {
			// Must be global unicast, not link-local, loopback, or private ULA (fc00::/7)
			if ip.IsGlobalUnicast() && !ip.IsPrivate() && !ip.IsLinkLocalUnicast() {
				return ip.String()
			}
		}
	}

	return ""
}
