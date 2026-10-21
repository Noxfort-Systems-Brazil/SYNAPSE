// SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
// Copyright (C) 2026 Noxfort Systems
//
// File: synapse-go/internal/tunnel/duckdns_test.go

package tunnel

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestCleanDuckDNSTokenAndDomain(t *testing.T) {
	tok := CleanDuckDNSToken("  \"a1b2c3d4-e5f6\"  ")
	if tok != "a1b2c3d4-e5f6" {
		t.Errorf("expected clean token, got '%s'", tok)
	}

	dom := CleanDuckDNSDomain("https://prefeitura-apucarana.duckdns.org/")
	if dom != "prefeitura-apucarana" {
		t.Errorf("expected 'prefeitura-apucarana', got '%s'", dom)
	}

	dom2 := CleanDuckDNSDomain("prefeitura-teste")
	if dom2 != "prefeitura-teste" {
		t.Errorf("expected 'prefeitura-teste', got '%s'", dom2)
	}
}

func TestDuckDNSExecuteUpdate(t *testing.T) {
	ts := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		dom := r.URL.Query().Get("domains")
		tok := r.URL.Query().Get("token")
		if dom == "validdomain" && tok == "validtoken" {
			w.WriteHeader(http.StatusOK)
			_, _ = w.Write([]byte("OK"))
		} else {
			w.WriteHeader(http.StatusOK)
			_, _ = w.Write([]byte("KO"))
		}
	}))
	defer ts.Close()

	driver := NewDuckDNSDriver(nil)
	driver.updateURL = ts.URL

	ctx := context.Background()

	// 1. Success case
	err := driver.executeUpdate(ctx, "validdomain", "validtoken", "")
	if err != nil {
		t.Fatalf("expected update to succeed, got %v", err)
	}

	// 2. Failure case
	errBad := driver.executeUpdate(ctx, "invaliddomain", "badtoken", "")
	if errBad == nil {
		t.Fatalf("expected update to fail on KO response")
	}
}
