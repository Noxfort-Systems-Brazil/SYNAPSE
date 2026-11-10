// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

package tunnel

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// ResolveDefaultCaddyPath locates the bundled Caddy binary in candidate directories.
func ResolveDefaultCaddyPath() string {
	candidates := []string{
		"bin/caddy",
		"../bin/caddy",
		"../../bin/caddy",
	}
	for _, c := range candidates {
		if fi, err := os.Stat(c); err == nil && !fi.IsDir() {
			abs, err := filepath.Abs(c)
			if err == nil {
				return abs
			}
			return c
		}
	}
	return "bin/caddy"
}

// ResolveDefaultCaddyfilePath locates the candidate Caddyfile configuration location.
func ResolveDefaultCaddyfilePath() string {
	candidates := []string{
		"config/Caddyfile",
		"../config/Caddyfile",
		"../../config/Caddyfile",
	}
	for _, c := range candidates {
		dir := filepath.Dir(c)
		if fi, err := os.Stat(dir); err == nil && fi.IsDir() {
			abs, err := filepath.Abs(c)
			if err == nil {
				return abs
			}
			return c
		}
	}
	return "config/Caddyfile"
}

// GenerateCaddyfileContent formats and writes the Caddyfile mapping DuckDNS to the local gateway.
func GenerateCaddyfileContent(destPath, subdomain string, targetPort, httpsPort int, token string) (string, error) {
	cleanSub := CleanDuckDNSDomain(subdomain)
	if cleanSub == "" {
		return "", fmt.Errorf("caddy subdomain cannot be empty")
	}

	cleanTok := CleanDuckDNSToken(token)
	fullDomain := fmt.Sprintf("%s.duckdns.org", cleanSub)

	if targetPort <= 0 {
		targetPort = 8081
	}
	if httpsPort <= 0 {
		httpsPort = 443
	}

	var globalOpts []string
	globalOpts = append(globalOpts, "admin off")
	globalOpts = append(globalOpts, "auto_https disable_redirects")
	if httpsPort != 443 {
		globalOpts = append(globalOpts, fmt.Sprintf("https_port %d", httpsPort))
	}

	siteLabel := fullDomain
	if httpsPort != 443 {
		siteLabel = fmt.Sprintf("%s:%d", fullDomain, httpsPort)
	}

	tlsBlock := ""
	if cleanTok != "" {
		tlsBlock = fmt.Sprintf("    tls {\n        dns duckdns %s\n    }\n", cleanTok)
	}

	content := fmt.Sprintf(`{
    %s
}

%s {
%s    reverse_proxy localhost:%d
}
`, strings.Join(globalOpts, "\n    "), siteLabel, tlsBlock, targetPort)

	dir := filepath.Dir(destPath)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return "", fmt.Errorf("failed to create caddyfile directory: %w", err)
	}

	if err := os.WriteFile(destPath, []byte(content), 0644); err != nil {
		return "", fmt.Errorf("failed to write caddyfile: %w", err)
	}

	return destPath, nil
}
