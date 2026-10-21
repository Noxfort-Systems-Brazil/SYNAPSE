// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { IBridgeEventHandler, LogLevel } from '../types';
import { DataSourceItem, EngineDataPayload } from '../../../types/sensors';

export interface ISensorsEventSink {
  handleEngineDataPayload: (payload: EngineDataPayload) => void;
  addSourceItem: (item: DataSourceItem) => void;
  removeSourceItem: (id: string) => void;
  associateSourceToElement: (sourceId: string, elementId: string) => void;
  addLog: (level: LogLevel, message: string) => void;
}

/**
 * Single Responsibility (SRP): Processes telemetry data streams, sensor registrations, and topology associations.
 */
export class SensorsEventHandler implements IBridgeEventHandler {
  readonly events = [
    'synapse:engine_data',
    'synapse:global_results',
    'synapse:drift_update',
    'synapse:source_added',
    'synapse:source_removed',
    'synapse:source_associated',
  ] as const;

  constructor(private readonly sink: ISensorsEventSink) {}

  handle(event: string, payload: any): void {
    switch (event) {
      case 'synapse:engine_data':
      case 'synapse:global_results':
      case 'synapse:drift_update':
        this.sink.handleEngineDataPayload(payload);
        break;

      case 'synapse:source_added': {
        const s = payload || {};
        const newSrc: DataSourceItem = {
          id: s.id,
          name: s.name,
          is_local: s.is_local ?? true,
          status: (s.status as any) || 'Active',
          source_type: s.source_type,
          connection_string: s.connection_string,
          quality: 100,
          semantic_type: s.semantic_type || 'Traffic Speed',
          latest_value: 0,
        };
        this.sink.addSourceItem(newSrc);
        break;
      }

      case 'synapse:source_removed':
        if (payload?.id) {
          this.sink.removeSourceItem(payload.id);
        }
        break;

      case 'synapse:source_associated':
        if (payload?.source_id && payload?.element_id) {
          this.sink.associateSourceToElement(payload.source_id, payload.element_id);
          this.sink.addLog('INFO', `Sensor '${payload.source_id}' associado ao elemento '${payload.element_id}'`);
        }
        break;
    }
  }
}
