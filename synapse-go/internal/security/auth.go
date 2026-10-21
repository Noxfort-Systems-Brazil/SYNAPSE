// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

package security

import (
	"net/http"
	"strings"
)

// Authenticator validates incoming sensor request credentials.
type Authenticator struct {
	expectedKey string
}

// NewAuthenticator creates a new Authenticator. If expectedKey is empty, authentication is disabled.
func NewAuthenticator(expectedKey string) *Authenticator {
	return &Authenticator{
		expectedKey: strings.TrimSpace(expectedKey),
	}
}

// IsEnabled returns true if authentication is active.
func (a *Authenticator) IsEnabled() bool {
	return a.expectedKey != ""
}

// Validate checks whether the request contains a valid Bearer token or X-API-Key header.
func (a *Authenticator) Validate(r *http.Request) bool {
	if !a.IsEnabled() {
		return true
	}

	authHeader := r.Header.Get("Authorization")
	if strings.HasPrefix(authHeader, "Bearer ") {
		token := strings.TrimSpace(strings.TrimPrefix(authHeader, "Bearer "))
		if token == a.expectedKey {
			return true
		}
	}

	if apiKey := strings.TrimSpace(r.Header.Get("X-API-Key")); apiKey == a.expectedKey {
		return true
	}

	return false
}
