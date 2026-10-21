// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { IStateHydrator, IStateHydratorSink } from './types';

export interface ISystemServiceHydration {
  getSystemStatus: () => Promise<any>;
  getDatabaseConfig: () => Promise<any>;
  getTelemetryConfig: () => Promise<any>;
}

export interface ITopologyServiceHydration {
  getTopology: () => Promise<any>;
}

export interface ISensorServiceHydration {
  getSources: () => Promise<any>;
}

/**
 * Single Responsibility Principle (SRP):
 * Synchronizes persisted backend state (phases, road topology, sensors, DB, and MQTT configs)
 * into the frontend reactive state stores upon initial connection.
 */
export class StateHydrator implements IStateHydrator {
  constructor(
    private readonly systemService: ISystemServiceHydration,
    private readonly topologyService: ITopologyServiceHydration,
    private readonly sensorService: ISensorServiceHydration,
    private readonly sink: IStateHydratorSink
  ) {}

  async hydrate(): Promise<void> {
    try {
      // 1. Sync System Phase & Artifacts from Disk
      const sysStatus = await this.systemService.getSystemStatus();
      if (sysStatus?.phase) {
        this.sink.setPhase(sysStatus.phase);
        if (sysStatus.completed_phases && sysStatus.completed_phases.length > 0) {
          this.sink.addLog(
            'INFO',
            `⚡ Auto-Progression: Fases completas no disco: [${sysStatus.completed_phases.join(', ')}]. Fase atual: ${sysStatus.phase}`
          );
        }
      }
      if (sysStatus?.has_dataset) {
        this.sink.setHasDataset?.(true);
        this.sink.addLog('INFO', '📦 Dataset Parquet histórico detectado no Data Lake.');
      }

      // 2. Sync Topology & Road Network
      const topo = await this.topologyService.getTopology();
      if (topo?.nodes && topo?.edges && topo.nodes.length > 0) {
        this.sink.setTopology(topo.nodes, topo.edges);
        this.sink.addLog('INFO', `🗺️ Topologia viária restaurada: ${topo.nodes.length} cruzamentos, ${topo.edges.length} vias.`);
      }

      // 3. Sync Sensors & Data Sources
      const srcs = await this.sensorService.getSources();
      if (Array.isArray(srcs) && srcs.length > 0) {
        this.sink.setSources(srcs);
        this.sink.addLog('INFO', `📡 ${srcs.length} sensor(es) restaurados do disco.`);
      }

      // 4. Sync Database Status from Disk
      try {
        const dbCfg = await this.systemService.getDatabaseConfig();
        if (dbCfg?.connected) {
          this.sink.setDbStatus({
            connected: true,
            message: `Conectado ao schema '${dbCfg.schema || 'schema_synapse'}'`,
          });
          this.sink.addLog('INFO', `🗄️ Banco de Dados PostgreSQL conectado ao schema '${dbCfg.schema || 'schema_synapse'}'.`);
        } else {
          this.sink.setDbStatus({
            connected: false,
            message: 'Desconectado',
          });
        }
      } catch {}

      // 5. Sync Monitor / Telemetry Status from Disk
      try {
        const teleCfg = await this.systemService.getTelemetryConfig();
        if (teleCfg) {
          this.sink.setMonitorStatus({
            connected: !!teleCfg.connected,
            ip: teleCfg.ip || 'localhost',
            host: teleCfg.host || 'localhost',
            port: teleCfg.port || 1883,
            message: teleCfg.connected ? `Conectado em ${teleCfg.ip || teleCfg.host}` : 'Desconectado',
          });
          if (teleCfg.connected) {
            this.sink.addLog(
              'INFO',
              `📶 Telemetria Externa (Monitor) conectada ao broker MQTT em ${teleCfg.ip || teleCfg.host}:${teleCfg.port || 1883}.`
            );
          }
        }
      } catch {}
    } catch (err: any) {
      this.sink.addLog('WARN', `Initial state sync note: ${err?.message || err}`);
    }
  }
}
