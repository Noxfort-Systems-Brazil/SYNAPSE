// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

package pipe

import (
	"bufio"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"os"
	"sync"
	"sync/atomic"
	"time"

	"synapse-gateway/internal/domain"
)

// Controller manages thread-safe STDOUT broadcasting and STDIN command processing.
type Controller struct {
	stdoutWriter io.Writer
	stdinReader  io.Reader
	writeMu      sync.Mutex
	stopCh       chan struct{}
	stopOnce     sync.Once

	startTime     time.Time
	totalRequests atomic.Uint64
	totalBytes    atomic.Uint64

	onShutdown func()
	onCommand  func(cmd domain.IPCCommand)
	logger     *log.Logger
}

// NewController initializes the pipe controller with OS streams.
func NewController(stdin io.Reader, stdout io.Writer, onShutdown func()) *Controller {
	if stdin == nil {
		stdin = os.Stdin
	}
	if stdout == nil {
		stdout = os.Stdout
	}
	return &Controller{
		stdinReader:  stdin,
		stdoutWriter: stdout,
		stopCh:       make(chan struct{}),
		startTime:    time.Now(),
		onShutdown:   onShutdown,
		logger:       log.New(os.Stderr, "[synapse-go-ipc] ", log.Ltime|log.Lmicroseconds),
	}
}

// SetCommandHandler registers a handler for application-specific commands (e.g. Poller, MQTT).
func (c *Controller) SetCommandHandler(handler func(cmd domain.IPCCommand)) {
	c.onCommand = handler
}

// EmitPacket writes an ingested sensor packet to STDOUT as NDJSON.
func (c *Controller) EmitPacket(sourceID string, rawPayload []byte, clientIP, contentType string) error {
	c.totalRequests.Add(1)
	c.totalBytes.Add(uint64(len(rawPayload)))

	ts := float64(time.Now().UnixNano()) / 1e9
	msg := domain.IPCMessage{
		Event:       "PACKET",
		SourceID:    sourceID,
		Payload:     json.RawMessage(rawPayload),
		ClientIP:    clientIP,
		Timestamp:   ts,
		Transport:   "HTTP-Push-Go",
		ContentType: contentType,
	}

	data, err := json.Marshal(msg)
	if err != nil {
		return err
	}

	c.writeMu.Lock()
	defer c.writeMu.Unlock()

	_, err = fmt.Fprintf(c.stdoutWriter, "%s\n", data)
	return err
}

// EmitEvent sends a generic system event to Python via STDOUT.
func (c *Controller) EmitEvent(event string, status string, errMsg string) error {
	msg := domain.IPCMessage{
		Event:  event,
		Status: status,
		Error:  errMsg,
	}

	data, err := json.Marshal(msg)
	if err != nil {
		return err
	}

	c.writeMu.Lock()
	defer c.writeMu.Unlock()

	_, err = fmt.Fprintf(c.stdoutWriter, "%s\n", data)
	return err
}

// EmitMessage sends any arbitrary IPCMessage to Python via STDOUT in a thread-safe manner.
func (c *Controller) EmitMessage(msg domain.IPCMessage) error {
	data, err := json.Marshal(msg)
	if err != nil {
		return err
	}

	c.writeMu.Lock()
	defer c.writeMu.Unlock()

	_, err = fmt.Fprintf(c.stdoutWriter, "%s\n", data)
	return err
}

// EmitStats sends live metrics to Python via STDOUT.
func (c *Controller) EmitStats() error {
	stats := &domain.GatewayStats{
		TotalRequests: c.totalRequests.Load(),
		TotalBytes:    c.totalBytes.Load(),
		UptimeSec:     time.Since(c.startTime).Seconds(),
	}

	msg := domain.IPCMessage{
		Event: "STATS",
		Stats: stats,
	}

	data, err := json.Marshal(msg)
	if err != nil {
		return err
	}

	c.writeMu.Lock()
	defer c.writeMu.Unlock()

	_, err = fmt.Fprintf(c.stdoutWriter, "%s\n", data)
	return err
}

// StartStdinLoop blocks reading STDIN commands line-by-line until EOF or error.
func (c *Controller) StartStdinLoop() {
	scanner := bufio.NewScanner(c.stdinReader)
	buf := make([]byte, 64*1024)
	scanner.Buffer(buf, 2*1024*1024)

	for scanner.Scan() {
		line := scanner.Bytes()
		if len(line) == 0 {
			continue
		}

		var cmd domain.IPCCommand
		if err := json.Unmarshal(line, &cmd); err != nil {
			_ = c.EmitEvent("ERROR", "INVALID_COMMAND", err.Error())
			continue
		}

		c.handleCommand(cmd)
	}

	if err := scanner.Err(); err != nil {
		c.logger.Printf("STDIN scanner error: %v", err)
	}

	c.logger.Println("STDIN pipe reached EOF. Initiating graceful shutdown...")
	c.Stop()
}

func (c *Controller) handleCommand(cmd domain.IPCCommand) {
	switch cmd.Cmd {
	case "PING":
		_ = c.EmitEvent("PONG", "OK", "")
	case "GET_STATS":
		_ = c.EmitStats()
	case "SHUTDOWN":
		c.logger.Println("Received SHUTDOWN command from Python.")
		c.Stop()
	default:
		if c.onCommand != nil {
			c.onCommand(cmd)
		} else {
			c.logger.Printf("Unknown command received: %s", cmd.Cmd)
			_ = c.EmitEvent("ERROR", "UNKNOWN_COMMAND", fmt.Sprintf("command '%s' not recognized", cmd.Cmd))
		}
	}
}

// Stop closes the stop channel and triggers shutdown callback.
func (c *Controller) Stop() {
	c.stopOnce.Do(func() {
		close(c.stopCh)
		if c.onShutdown != nil {
			c.onShutdown()
		}
	})
}

// Done returns a channel signaling when the controller stopped.
func (c *Controller) Done() <-chan struct{} {
	return c.stopCh
}
