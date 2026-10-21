// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { ITransportClient } from '../transport';
import { IConnectionHealthWatcher, IConnectionSink } from './types';

/**
 * Single Responsibility Principle (SRP):
 * Exclusively manages IPC handshake pings, RTT latency tracking, and continuous background heartbeats.
 */
export class ConnectionHealthWatcher implements IConnectionHealthWatcher {
  private isCleanedUp = false;
  private hasBootstrapped = false;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;

  constructor(
    private readonly transport: ITransportClient,
    private readonly sink: IConnectionSink,
    private readonly pingIntervalMs = 3000,
    private readonly maxStartupAttempts = 30,
    private readonly startupDelayMs = 500
  ) {}

  start(onConnected?: () => Promise<void> | void): void {
    this.isCleanedUp = false;
    this.probeConnection(onConnected);
  }

  dispose(): void {
    this.isCleanedUp = true;
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private async performPing(onConnected?: () => Promise<void> | void): Promise<boolean> {
    if (this.isCleanedUp) return false;
    try {
      const t0 = performance.now();
      const res = await this.transport.invoke<{ status?: string }>('ping');
      const rtt = Math.max(0.1, performance.now() - t0);
      this.sink.setLatencyMs(Number(rtt.toFixed(2)));

      if (res?.status === 'ok') {
        const wasConnected = this.sink.isConnected();
        this.sink.setConnected(true);

        if (!wasConnected || !this.hasBootstrapped) {
          this.sink.addLog('INFO', 'IPC Handshake established successfully.');
          this.hasBootstrapped = true;
          if (onConnected) {
            await onConnected();
          }
        }
        return true;
      }
    } catch (err) {
      console.warn('[ConnectionHealthWatcher] ⚠️ Falha no handshake/ping com o backend:', err);
      this.sink.setConnected(false);
    }
    return false;
  }

  private async probeConnection(onConnected?: () => Promise<void> | void): Promise<void> {
    // 1. Rapid polling during startup
    for (let attempt = 1; attempt <= this.maxStartupAttempts; attempt++) {
      if (this.isCleanedUp) break;
      const ok = await this.performPing(onConnected);
      if (ok) break;
      await new Promise((r) => setTimeout(r, this.startupDelayMs));
    }

    // 2. Continuous background heartbeat
    if (!this.isCleanedUp) {
      this.heartbeatTimer = setInterval(() => {
        if (!this.isCleanedUp) {
          this.performPing(onConnected);
        }
      }, this.pingIntervalMs);
    }
  }
}
