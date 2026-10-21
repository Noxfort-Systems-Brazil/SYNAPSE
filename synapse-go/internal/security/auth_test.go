// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

package security

import (
	"net/http/httptest"
	"testing"
)

func TestAuthenticator_OpenMode(t *testing.T) {
	auth := NewAuthenticator("")
	if auth.IsEnabled() {
		t.Errorf("expected disabled auth")
	}

	req := httptest.NewRequest("POST", "/src_1", nil)
	if !auth.Validate(req) {
		t.Errorf("expected open mode to allow all requests")
	}
}

func TestAuthenticator_ProtectedMode(t *testing.T) {
	auth := NewAuthenticator("my-secret-token")
	if !auth.IsEnabled() {
		t.Errorf("expected enabled auth")
	}

	// 1. Missing header
	req := httptest.NewRequest("POST", "/src_1", nil)
	if auth.Validate(req) {
		t.Errorf("expected request without token to fail")
	}

	// 2. Bearer token
	req.Header.Set("Authorization", "Bearer my-secret-token")
	if !auth.Validate(req) {
		t.Errorf("expected valid Bearer token to succeed")
	}

	// 3. X-API-Key header
	req2 := httptest.NewRequest("POST", "/src_1", nil)
	req2.Header.Set("X-API-Key", "my-secret-token")
	if !auth.Validate(req2) {
		t.Errorf("expected valid X-API-Key header to succeed")
	}
}
