// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { useSystemStore, useTopologyStore, useSensorsStore, useXaiStore, useEtlStore, initSynapseBridge } from '../stores';
import { getTransportClient } from '../services/transport';

/**
 * Facade Store for backward-compatibility.
 * Delegates all state and actions to granular SOLID stores and services.
 */
export const useSynapseStore = () => {
  const system = useSystemStore();
  const topology = useTopologyStore();
  const sensors = useSensorsStore();
  const xai = useXaiStore();
  const etl = useEtlStore();

  const transport = getTransportClient();

  const sendCommand = async (action: string, payload: any = {}) => {
    try {
      return await transport.invoke(action, payload);
    } catch (err: any) {
      system.addLog('ERROR', `IPC Command failed (${action}): ${err?.message || err}`);
      throw err;
    }
  };

  return {
    // System
    connected: system.connected,
    phase: system.phase,
    logs: system.logs,
    dbStatus: system.dbStatus,
    addLog: system.addLog,
    clearLogs: system.clearLogs,

    // Topology
    nodes: topology.nodes,
    edges: topology.edges,
    mapLoaded: topology.mapLoaded,
    selectedNodeId: topology.selectedNodeId,
    selectedEdgeId: topology.selectedEdgeId,
    isAssociatingSourceId: topology.isAssociatingSourceId,
    setTopology: topology.setTopology,
    setAssociatingSource: topology.setAssociatingSourceId,

    // Sensors & Telemetry
    sources: sensors.sources,
    selectedSourceId: sensors.selectedSourceId,
    latestEngineData: sensors.latestEngineData,
    lossHistory: sensors.lossHistory,
    driftHistory: sensors.driftHistory,
    fuserLossHistory: sensors.fuserLossHistory,
    fuserDriftHistory: sensors.fuserDriftHistory,
    setSelectedSource: sensors.setSelectedSourceId,

    // XAI
    verdicts: xai.verdicts,
    linguistLogs: xai.linguistLogs,
    xaiHistory: xai.xaiHistory,
    selectedXaiResultId: xai.selectedXaiResultId,
    setSelectedXaiResult: xai.setSelectedXaiResultId,

    // ETL
    parquetInspection: etl.parquetInspection,
    parquetProgress: etl.importProgress.progress,
    parquetStatus: etl.importProgress.status,

    // Actions & Bridge
    sendCommand,
    initBridge: initSynapseBridge,
  };
};
