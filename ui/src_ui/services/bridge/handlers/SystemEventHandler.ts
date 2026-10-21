// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { IBridgeEventHandler, LogLevel } from '../types';
import { SystemPhase } from '../../../types/system';
import { useSystemStore } from '../../../stores';

export interface ISystemEventSink {
  setConnected: (connected: boolean) => void;
  setPhase: (phase: SystemPhase) => void;
  addLog: (level: LogLevel, message: string) => void;
}

/**
 * Single Responsibility (SRP): Processes core system lifecycle, log messages, and phase transitions.
 */
export class SystemEventHandler implements IBridgeEventHandler {
  readonly events = [
    'synapse:ready',
    'synapse:disconnected',
    'synapse:log_message',
    'synapse:status_message',
    'synapse:phase_transition',
    'synapse:error_occurred',
  ] as const;

  constructor(
    private readonly sink: ISystemEventSink,
    private readonly onReady?: () => Promise<void> | void
  ) {}

  async handle(event: string, payload: any): Promise<void> {
    switch (event) {
      case 'synapse:ready':
        this.sink.setConnected(true);
        this.sink.addLog('INFO', `Backend Daemon Online (${JSON.stringify(payload)})`);
        if (this.onReady) {
          await this.onReady();
        }
        break;

      case 'synapse:disconnected':
        this.sink.setConnected(false);
        this.sink.addLog('ERROR', '🔴 Backend Daemon Offline: canal IPC encerrado.');
        break;

      case 'synapse:log_message':
        this.sink.addLog(payload?.level || 'INFO', payload?.message || String(payload));
        break;

      case 'synapse:status_message':
        this.sink.addLog('SYSTEM', payload?.message || String(payload));
        break;

      case 'synapse:phase_transition':
        if (payload?.phase) {
          this.sink.setPhase(payload.phase as SystemPhase);
          this.sink.addLog('SYSTEM', `Phase transitioned to: ${payload.phase}`);
        }
        break;

      case 'synapse:error_occurred': {
        const errorMsg = payload?.error || String(payload);
        this.sink.addLog('ERROR', errorMsg);
        const currentPhase = useSystemStore.getState().phase;
        if (currentPhase === 'RUNNING_OPTIMIZATION') {
          this.sink.setPhase('IDLE_OPTIMIZATION');
        } else if (currentPhase === 'RUNNING_OFFLINE') {
          this.sink.setPhase('IDLE_OFFLINE');
        } else if (currentPhase === 'RUNNING_ONLINE') {
          this.sink.setPhase('IDLE_ONLINE');
        }
        break;
      }
    }
  }
}
