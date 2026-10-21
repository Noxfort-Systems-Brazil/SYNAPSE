// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { IBridgeEventHandler, LogLevel } from '../types';

export interface ITopologyEventSink {
  setTopology: (nodes: any[], edges: any[]) => void;
  addLog: (level: LogLevel, message: string) => void;
}

/**
 * Single Responsibility (SRP): Processes road network topology loading events.
 */
export class TopologyEventHandler implements IBridgeEventHandler {
  readonly events = ['synapse:map_loaded'] as const;

  constructor(private readonly sink: ITopologyEventSink) {}

  handle(event: string, payload: any): void {
    if (event === 'synapse:map_loaded') {
      if (payload?.nodes && payload?.edges) {
        this.sink.setTopology(payload.nodes, payload.edges);
        this.sink.addLog('INFO', `Map loaded: ${payload.nodes.length} nodes, ${payload.edges.length} edges`);
      }
    }
  }
}
