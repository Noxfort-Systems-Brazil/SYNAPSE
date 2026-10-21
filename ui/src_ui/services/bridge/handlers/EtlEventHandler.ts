// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { IBridgeEventHandler, LogLevel } from '../types';

export interface IEtlEventSink {
  setImportProgress: (progress: { progress: number; status?: string; isImporting: boolean }) => void;
  addLog: (level: LogLevel, message: string) => void;
}

/**
 * Single Responsibility (SRP): Processes Parquet / dataset asynchronous ingestion progress and completion.
 */
export class EtlEventHandler implements IBridgeEventHandler {
  readonly events = [
    'synapse:import_progress',
    'synapse:import_finished',
  ] as const;

  constructor(private readonly sink: IEtlEventSink) {}

  handle(event: string, payload: any): void {
    switch (event) {
      case 'synapse:import_progress':
        this.sink.setImportProgress({
          progress: payload?.progress || 0,
          isImporting: true,
        });
        break;

      case 'synapse:import_finished': {
        const res = payload || {};
        this.sink.setImportProgress({
          progress: res.success ? 100 : 0,
          status: res.message,
          isImporting: false,
        });
        this.sink.addLog(res.success ? 'INFO' : 'ERROR', `Dataset Ingestion: ${res.message}`);
        break;
      }
    }
  }
}
