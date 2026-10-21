// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

package mqtt

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"strings"
	"sync"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"
	"synapse-gateway/internal/transport/pipe"
)

// Config encapsulates parameters for the MQTT transport client.
type Config struct {
	BrokerHost string
	BrokerPort int
	ClientID   string
	Username   string
	Password   string
	Topics     []string
}

// Client manages connection to the MQTT broker and routes messages to PipeController.
type Client struct {
	cfg    Config
	pipe   *pipe.Controller
	client mqtt.Client
	logger *log.Logger
	mu     sync.RWMutex
}

// NewClient initializes the MQTT client.
func NewClient(cfg Config, p *pipe.Controller) *Client {
	if cfg.BrokerHost == "" {
		cfg.BrokerHost = "localhost"
	}
	if cfg.BrokerPort <= 0 {
		cfg.BrokerPort = 1883
	}
	if cfg.ClientID == "" {
		cfg.ClientID = fmt.Sprintf("synapse-gateway-%d", time.Now().UnixNano()%10000)
	}
	if len(cfg.Topics) == 0 {
		cfg.Topics = []string{
			"synapse/+/telemetry",
			"traffic/cameras/#",
			"noxfort/telemetry/#",
		}
	}

	return &Client{
		cfg:    cfg,
		pipe:   p,
		logger: log.New(os.Stderr, "[synapse-go-mqtt] ", log.Ltime|log.Lmicroseconds),
	}
}

// Start begins connecting asynchronously with automatic background retries.
func (c *Client) Start() {
	opts := mqtt.NewClientOptions()
	brokerURL := fmt.Sprintf("tcp://%s:%d", c.cfg.BrokerHost, c.cfg.BrokerPort)
	opts.AddBroker(brokerURL)
	opts.SetClientID(c.cfg.ClientID)
	opts.SetAutoReconnect(true)
	opts.SetConnectRetry(true)
	opts.SetConnectRetryInterval(5 * time.Second)
	opts.SetKeepAlive(30 * time.Second)

	if c.cfg.Username != "" {
		opts.SetUsername(c.cfg.Username)
		opts.SetPassword(c.cfg.Password)
	}

	opts.SetOnConnectHandler(c.onConnect)
	opts.SetConnectionLostHandler(c.onConnectionLost)

	c.mu.Lock()
	c.client = mqtt.NewClient(opts)
	c.mu.Unlock()

	c.logger.Printf("Connecting to MQTT broker at %s (ClientID: %s)...", brokerURL, c.cfg.ClientID)
	go func() {
		token := c.client.Connect()
		if token.WaitTimeout(3 * time.Second) {
			if err := token.Error(); err != nil {
				c.logger.Printf("ℹ️ Initial MQTT connection to %s failed (%v). Background auto-reconnect active.", brokerURL, err)
			}
		}
	}()
}

func (c *Client) onConnect(client mqtt.Client) {
	c.logger.Printf("✅ Connected to MQTT broker. Subscribing to topics: %v", c.cfg.Topics)
	_ = c.pipe.EmitEvent("MQTT_CONNECTED", "CONNECTED", "")

	for _, topic := range c.cfg.Topics {
		token := client.Subscribe(topic, 1, c.handleMessage)
		if token.Wait() && token.Error() != nil {
			c.logger.Printf("⚠️ Failed to subscribe to topic '%s': %v", topic, token.Error())
		} else {
			c.logger.Printf("📡 Subscribed to MQTT topic: %s", topic)
		}
	}
}

func (c *Client) onConnectionLost(client mqtt.Client, err error) {
	c.logger.Printf("⚠️ MQTT connection lost: %v. Reconnecting automatically...", err)
	_ = c.pipe.EmitEvent("MQTT_CONNECTION_LOST", "RECONNECTING", err.Error())
}

func (c *Client) handleMessage(client mqtt.Client, msg mqtt.Message) {
	rawPayload := msg.Payload()
	if len(rawPayload) == 0 {
		return
	}

	sourceID := c.resolveSourceID(msg.Topic(), rawPayload)

	normalized := rawPayload
	if !json.Valid(rawPayload) {
		escaped, _ := json.Marshal(string(rawPayload))
		normalized = escaped
	}

	originMeta := fmt.Sprintf("mqtt://%s", msg.Topic())
	if err := c.pipe.EmitPacket(sourceID, normalized, originMeta, "application/json"); err != nil {
		c.logger.Printf("Failed to emit MQTT packet to pipe: %v", err)
	}
}

// resolveSourceID extracts device identity from payload or topic pattern.
func (c *Client) resolveSourceID(topic string, payload []byte) string {
	var obj map[string]any
	if err := json.Unmarshal(payload, &obj); err == nil {
		candidates := []string{"sensor_id", "source_id", "id", "origin", "camera_id", "device_id"}
		for _, key := range candidates {
			if val, ok := obj[key]; ok {
				if strVal, isStr := val.(string); isStr && strVal != "" {
					return strVal
				}
			}
		}
	}

	// Heuristic: Extract intermediate segment from topic (e.g. traffic/cameras/cam_42/telemetry -> cam_42)
	parts := strings.Split(strings.Trim(topic, "/"), "/")
	if len(parts) >= 2 {
		for i := len(parts) - 1; i >= 0; i-- {
			p := parts[i]
			if p != "telemetry" && p != "data" && p != "events" && p != "status" {
				return p
			}
		}
	}

	return "mqtt_" + strings.ReplaceAll(topic, "/", "_")
}

// Stop disconnects the MQTT client gracefully.
func (c *Client) Stop() {
	c.mu.Lock()
	defer c.mu.Unlock()

	if c.client != nil && c.client.IsConnected() {
		c.logger.Println("Disconnecting from MQTT broker...")
		c.client.Disconnect(200)
	}
}
