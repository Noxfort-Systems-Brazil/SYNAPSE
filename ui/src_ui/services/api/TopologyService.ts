// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { ITransportClient, getTransportClient } from '../transport';
import { TopologyPayload } from '../../types/topology';
import { useTopologyStore } from '../../stores/useTopologyStore';

export class TopologyService {
  constructor(private transport: ITransportClient = getTransportClient()) {}

  async loadMap(path: string): Promise<TopologyPayload> {
    const res = await this.transport.invoke<any, TopologyPayload>('load_map', { path });
    if (res && Array.isArray(res.nodes) && Array.isArray(res.edges)) {
      useTopologyStore.getState().setTopology(res.nodes, res.edges);
    }
    return res;
  }

  async getTopology(): Promise<TopologyPayload> {
    const res = await this.transport.invoke<any, TopologyPayload>('get_topology');
    if (res && Array.isArray(res.nodes) && Array.isArray(res.edges)) {
      useTopologyStore.getState().setTopology(res.nodes, res.edges);
    }
    return res;
  }
}

export const topologyService = new TopologyService();
