// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"strconv"
	"syscall"
	"time"

	"synapse-gateway/internal/config"
	"synapse-gateway/internal/domain"
	"synapse-gateway/internal/security"
	transportHttp "synapse-gateway/internal/transport/http"
	transportMqtt "synapse-gateway/internal/transport/mqtt"
	transportPipe "synapse-gateway/internal/transport/pipe"
	transportPoller "synapse-gateway/internal/transport/poller"
	transportVpn "synapse-gateway/internal/transport/vpn"
	"synapse-gateway/internal/tunnel"
)

func main() {
	cfg := config.Load(os.Args[1:])

	logger := log.New(os.Stderr, "[synapse-go] ", log.Ltime|log.Lmicroseconds)
	logger.Println("==========================================================")
	logger.Println("   SYNAPSE Ingestion Gateway — Zero-Port OS Anonymous Pipe")
	logger.Println("==========================================================")
	logger.Printf("Ingestion Host:   %s", cfg.Host)
	logger.Printf("Ingestion Port:   %d", cfg.Port)

	auth := security.NewAuthenticator(cfg.APIKey)
	if auth.IsEnabled() {
		logger.Println("Authentication:   ACTIVE (API Key / Bearer Protected)")
	} else {
		logger.Println("Authentication:   OPEN (Local / Unauthenticated Mode)")
	}

	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, os.Interrupt, syscall.SIGTERM)

	pipeCtrl := transportPipe.NewController(os.Stdin, os.Stdout, func() {
		// Callback triggered when STDIN pipe is closed by parent Python process (EOF)
		select {
		case sigCh <- syscall.SIGTERM:
		default:
		}
	})

	// 1. Initialize HTTP Push Server
	server := transportHttp.NewServer(cfg, auth, pipeCtrl)
	if err := server.Start(); err != nil {
		logger.Fatalf("[FATAL] Failed to start Ingestion Gateway: %v", err)
	}

	// 2. Initialize HTTP Poller Engine (for Global External APIs)
	pollEngine := transportPoller.NewPoller(pipeCtrl)

	// 3. Initialize MQTT Subscriber (for IoT & Edge Devices)
	var mqttClient *transportMqtt.Client
	if cfg.EnableMQTT {
		mqttClient = transportMqtt.NewClient(transportMqtt.Config{
			BrokerHost: cfg.MQTTHost,
			BrokerPort: cfg.MQTTPort,
		}, pipeCtrl)
		mqttClient.Start()
	}

	// 4. Initialize WireGuard VPN Manager (if enabled)
	var vpnMgr transportVpn.IVPNManager
	if cfg.EnableVPN {
		var err error
		vpnMgr, err = transportVpn.NewDefaultManager(transportVpn.Config{
			InterfaceName: cfg.VPNInterface,
			Port:          cfg.VPNPort,
			ServerIP:      cfg.VPNIP,
			Endpoint:      cfg.VPNEndpoint,
			StoragePath:   cfg.VPNStorage,
		})
		if err != nil {
			logger.Printf("⚠️ [synapse-go-vpn] Could not initialize VPN manager: %v", err)
		} else {
			if err := vpnMgr.Start(); err != nil {
				logger.Printf("⚠️ [synapse-go-vpn] VPN start error: %v", err)
			}
		}
	}

	// 5. Initialize DuckDNS Dynamic DNS Driver & Caddy Reverse Proxy Manager
	duckDriver := tunnel.NewDuckDNSDriver(pipeCtrl)
	caddyMgr := tunnel.NewCaddyManager("", "", pipeCtrl)

	// 6. Command Router for Dynamic Source Management via STDIN
	pipeCtrl.SetCommandHandler(func(cmd domain.IPCCommand) {
		switch cmd.Cmd {
		case "REGISTER_POLL_SOURCE":
			pollEngine.Register(cmd.SourceID, cmd.URL, cmd.IntervalSec)
		case "UNREGISTER_POLL_SOURCE":
			pollEngine.Unregister(cmd.SourceID)
		case "SET_DUCKDNS":
			if cmd.Enabled {
				if err := duckDriver.Start(cmd.Domain, cmd.Token, cmd.Port); err != nil {
					logger.Printf("⚠️ [synapse-go-duckdns] Failed to start DuckDNS: %v", err)
				}
				if cmd.CaddyEnabled {
					targetPort := 8081
					if p, err := strconv.Atoi(cmd.Port); err == nil && p > 0 {
						targetPort = p
					}
					httpsPort := 443
					if cmd.HTTPSPort > 0 {
						httpsPort = cmd.HTTPSPort
					}
					if err := caddyMgr.Start(cmd.Domain, targetPort, httpsPort, cmd.Token); err != nil {
						logger.Printf("⚠️ [synapse-go-caddy] Failed to start Caddy: %v", err)
					}
				} else {
					_ = caddyMgr.Stop()
				}
			} else {
				_ = duckDriver.Stop()
				_ = caddyMgr.Stop()
			}
		case "STOP_DUCKDNS":
			_ = duckDriver.Stop()
			_ = caddyMgr.Stop()
		case "TEST_DUCKDNS":
			go duckDriver.TestConnection(cmd.Domain, cmd.Token)
		case "REGISTER_VPN_PEER":
			if vpnMgr != nil {
				targetID := cmd.SourceID
				if targetID == "" {
					targetID = cmd.PeerID
				}
				peer, clientConf, err := vpnMgr.RegisterPeer(targetID)
				if err != nil {
					_ = pipeCtrl.EmitEvent("ERROR", "VPN_PEER_ERROR", err.Error())
				} else {
					_ = pipeCtrl.EmitMessage(domain.IPCMessage{
						Event:        "VPN_PEER_REGISTERED",
						SourceID:     targetID,
						ClientIP:     peer.IP,
						PublicKey:    peer.PublicKey,
						ClientConfig: clientConf,
						Status:       "REGISTERED",
					})
				}
			} else {
				_ = pipeCtrl.EmitEvent("ERROR", "VPN_DISABLED", "WireGuard VPN is disabled")
			}
		case "UNREGISTER_VPN_PEER":
			if vpnMgr != nil {
				targetID := cmd.SourceID
				if targetID == "" {
					targetID = cmd.PeerID
				}
				_ = vpnMgr.RemovePeer(targetID)
				_ = pipeCtrl.EmitEvent("VPN_PEER_UNREGISTERED", "SUCCESS", "")
			}
		default:
			logger.Printf("Unhandled custom command: %s", cmd.Cmd)
		}
	})

	// Read STDIN in background for control commands or EOF detection
	go pipeCtrl.StartStdinLoop()

	// Wait for OS signal or Stdin EOF
	sig := <-sigCh
	logger.Printf("Received termination signal '%v'. Initiating graceful shutdown...", sig)

	// Graceful Teardown of all transports
	_ = caddyMgr.Stop()
	_ = duckDriver.Stop()
	pollEngine.StopAll()
	if mqttClient != nil {
		mqttClient.Stop()
	}
	if vpnMgr != nil {
		_ = vpnMgr.Close()
	}

	shutdownCtx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()

	if err := server.Stop(shutdownCtx); err != nil {
		logger.Printf("Error during HTTP server shutdown: %v", err)
	}

	logger.Println("SYNAPSE Ingestion Gateway stopped successfully.")
}
