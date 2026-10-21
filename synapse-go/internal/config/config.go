// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

package config

import (
	"flag"
	"os"
	"strconv"
	"time"
)

// Config encapsulates all runtime configuration options for the Ingestion Gateway.
type Config struct {
	Host           string
	Port           int
	APIKey         string
	MaxPayloadSize int64
	ReadTimeout    time.Duration
	WriteTimeout   time.Duration
	IdleTimeout    time.Duration

	// MQTT Settings
	EnableMQTT bool
	MQTTHost   string
	MQTTPort   int

	// WireGuard VPN Settings
	EnableVPN    bool
	VPNPort      int
	VPNIP        string
	VPNInterface string
	VPNEndpoint  string
	VPNStorage   string
}

func getEnv(key, fallback string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return fallback
}

// Load parses environment variables and CLI arguments into a structured Config.
func Load(args []string) *Config {
	defaultHost := getEnv("SYNAPSE_GATEWAY_HOST", "0.0.0.0")
	defaultPortStr := getEnv("SYNAPSE_GATEWAY_PORT", "8081")
	defaultPort, _ := strconv.Atoi(defaultPortStr)
	if defaultPort <= 0 {
		defaultPort = 8081
	}
	defaultAPIKey := getEnv("SYNAPSE_GATEWAY_API_KEY", "")

	defaultMQTTHost := getEnv("SYNAPSE_MQTT_HOST", "localhost")
	defaultMQTTPortStr := getEnv("SYNAPSE_MQTT_PORT", "1883")
	defaultMQTTPort, _ := strconv.Atoi(defaultMQTTPortStr)
	if defaultMQTTPort <= 0 {
		defaultMQTTPort = 1883
	}

	defaultEnableMQTTStr := getEnv("SYNAPSE_ENABLE_MQTT", "true")
	defaultEnableMQTT := defaultEnableMQTTStr == "true" || defaultEnableMQTTStr == "1" || defaultEnableMQTTStr == "yes"

	defaultEnableVPNStr := getEnv("SYNAPSE_ENABLE_VPN", "true")
	defaultEnableVPN := defaultEnableVPNStr == "true" || defaultEnableVPNStr == "1" || defaultEnableVPNStr == "yes"

	defaultVPNPortStr := getEnv("SYNAPSE_VPN_PORT", "51820")
	defaultVPNPort, _ := strconv.Atoi(defaultVPNPortStr)
	if defaultVPNPort <= 0 {
		defaultVPNPort = 51820
	}
	defaultVPNIP := getEnv("SYNAPSE_VPN_IP", "10.10.0.1/24")
	defaultVPNInterface := getEnv("SYNAPSE_VPN_INTERFACE", "wg0")
	defaultVPNEndpoint := getEnv("SYNAPSE_VPN_ENDPOINT", "127.0.0.1:51820")
	defaultVPNStorage := getEnv("SYNAPSE_VPN_STORAGE", "config/vpn_state.json")

	fs := flag.NewFlagSet("synapse-gateway", flag.ContinueOnError)
	host := fs.String("host", defaultHost, "Bind address for incoming sensors")
	port := fs.Int("port", defaultPort, "Listening port for HTTP sensor ingestion")
	apiKey := fs.String("api-key", defaultAPIKey, "Optional API key / Bearer token for authentication")
	enableMQTT := fs.Bool("enable-mqtt", defaultEnableMQTT, "Enable native MQTT ingestion client")
	mqttHost := fs.String("mqtt-host", defaultMQTTHost, "MQTT broker host")
	mqttPort := fs.Int("mqtt-port", defaultMQTTPort, "MQTT broker port")

	enableVPN := fs.Bool("enable-vpn", defaultEnableVPN, "Enable native WireGuard VPN server")
	vpnPort := fs.Int("vpn-port", defaultVPNPort, "WireGuard UDP listen port")
	vpnIP := fs.String("vpn-ip", defaultVPNIP, "WireGuard server IP and subnet (CIDR)")
	vpnInterface := fs.String("vpn-interface", defaultVPNInterface, "WireGuard network interface name")
	vpnEndpoint := fs.String("vpn-endpoint", defaultVPNEndpoint, "Public IP or domain for peer client configs")
	vpnStorage := fs.String("vpn-storage", defaultVPNStorage, "Path to VPN persistent state JSON file")

	_ = fs.Parse(args)

	return &Config{
		Host:           *host,
		Port:           *port,
		APIKey:         *apiKey,
		MaxPayloadSize: 10 * 1024 * 1024, // 10MB
		ReadTimeout:    15 * time.Second,
		WriteTimeout:   15 * time.Second,
		IdleTimeout:    60 * time.Second,
		EnableMQTT:     *enableMQTT,
		MQTTHost:       *mqttHost,
		MQTTPort:       *mqttPort,
		EnableVPN:      *enableVPN,
		VPNPort:        *vpnPort,
		VPNIP:          *vpnIP,
		VPNInterface:   *vpnInterface,
		VPNEndpoint:    *vpnEndpoint,
		VPNStorage:     *vpnStorage,
	}
}
