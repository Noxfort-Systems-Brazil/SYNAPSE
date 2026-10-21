// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { create } from 'zustand';
import { DataSourceItem, EngineDataPayload, TelemetryPoint } from '../types/sensors';

export interface SensorsState {
  sources: DataSourceItem[];
  selectedSourceId: string | null;
  latestEngineData: EngineDataPayload | null;
  lossHistory: Record<string, TelemetryPoint[]>;
  driftHistory: Record<string, TelemetryPoint[]>;
  fuserLossHistory: TelemetryPoint[];
  fuserDriftHistory: TelemetryPoint[];

  // Actions
  setSources: (sources: DataSourceItem[]) => void;
  addSourceItem: (source: DataSourceItem) => void;
  removeSourceItem: (sourceId: string) => void;
  updateSourceItem: (sourceId: string, updates: Partial<DataSourceItem>) => void;
  associateSourceToElement: (sourceId: string, elementId: string) => void;
  disassociateSource: (sourceId: string) => void;
  setSelectedSourceId: (id: string | null) => void;
  handleEngineDataPayload: (data: EngineDataPayload) => void;
}

export const useSensorsStore = create<SensorsState>((set) => ({
  sources: [],
  selectedSourceId: null,
  latestEngineData: null,
  lossHistory: {},
  driftHistory: {},
  fuserLossHistory: [],
  fuserDriftHistory: [],

  setSources: (sources) => set({ sources }),

  addSourceItem: (source) =>
    set((state) => {
      const exists = state.sources.some((s) => s.id === source.id);
      if (exists) {
        return {
          sources: state.sources.map((s) =>
            s.id === source.id ? { ...s, ...source } : s
          ),
        };
      }
      return { sources: [...state.sources, source] };
    }),

  removeSourceItem: (sourceId) =>
    set((state) => ({
      sources: state.sources.filter((s) => s.id !== sourceId),
      selectedSourceId: state.selectedSourceId === sourceId ? null : state.selectedSourceId,
    })),

  updateSourceItem: (sourceId, updates) =>
    set((state) => ({
      sources: state.sources.map((s) => (s.id === sourceId ? ({ ...s, ...updates } as DataSourceItem) : s)),
    })),

  associateSourceToElement: (sourceId, elementId) =>
    set((state) => ({
      sources: state.sources.map((s) => (s.id === sourceId ? ({ ...s, associated_element: elementId } as DataSourceItem) : s)),
    })),

  disassociateSource: (sourceId) =>
    set((state) => ({
      sources: state.sources.map((s) => (s.id === sourceId ? ({ ...s, associated_element: undefined } as DataSourceItem) : s)),
    })),

  setSelectedSourceId: (id) => set({ selectedSourceId: id }),

  handleEngineDataPayload: (data: any) => {
    if (!data) return;
    const now = new Date().toLocaleTimeString();

    set((state) => {
      let currentSources = [...state.sources];
      const nextLoss = { ...state.lossHistory };
      const nextDrift = { ...state.driftHistory };
      let nextFuserLoss = [...state.fuserLossHistory];
      let nextFuserDrift = [...state.fuserDriftHistory];

      const targetSingleId = data.id || data.source_id || data.source;
      const isGlobalCycle = !targetSingleId && (data.loss !== undefined || data.losses !== undefined);

      // ── 1. Update Fuser Agent Global MLOps Telemetry (1 Hz authoritative neural cycle) ──
      if (isGlobalCycle) {
        const rawFuserLoss = data.loss ?? data.security_score;
        if (rawFuserLoss !== undefined && !isNaN(Number(rawFuserLoss))) {
          const pt = { time: now, value: Number(rawFuserLoss) };
          nextFuserLoss = [...nextFuserLoss, pt].slice(-30);
          nextLoss['fuser'] = nextFuserLoss;
        }

        const rawFuserDrift = data.drift;
        if (rawFuserDrift !== undefined && !isNaN(Number(rawFuserDrift))) {
          const pt = { time: now, value: Number(rawFuserDrift) };
          nextFuserDrift = [...nextFuserDrift, pt].slice(-30);
          nextDrift['fuser'] = nextFuserDrift;
        }
      }

      const updatedSources = currentSources.map((src) => {
        const isTarget = Boolean(targetSingleId && (targetSingleId === src.id || targetSingleId === src.name));

        // 1. Resolve Sensor Value
        let val = src.latest_value;
        if (isTarget) {
          if (data.raw !== undefined) val = Number(data.raw);
          else if (data.value !== undefined) val = Number(data.value);
          else if (data.val !== undefined) val = Number(data.val);
        } else if (data.sensor_snapshot?.[src.id] !== undefined) {
          const snap = data.sensor_snapshot[src.id];
          val = typeof snap === 'object' && snap !== null && snap.value !== undefined ? Number(snap.value) : Number(snap);
        } else if (data.sensor_snapshot?.[src.name] !== undefined) {
          const snap = data.sensor_snapshot[src.name];
          val = typeof snap === 'object' && snap !== null && snap.value !== undefined ? Number(snap.value) : Number(snap);
        } else if (src.associated_element && data.sensor_snapshot?.[src.associated_element] !== undefined) {
          const snap = data.sensor_snapshot[src.associated_element];
          val = typeof snap === 'object' && snap !== null && snap.value !== undefined ? Number(snap.value) : Number(snap);
        } else if (data.source_values?.[src.id] !== undefined) {
          val = Number(data.source_values[src.id]);
        } else if (data.edge_data?.[src.id]?.speed !== undefined) {
          val = Number(data.edge_data[src.id].speed);
        } else if (src.associated_element && data.edge_data?.[src.associated_element]?.speed !== undefined) {
          val = Number(data.edge_data[src.associated_element].speed);
        }

        // 2. Resolve Loss / Anomaly Score (Strictly isolated per sensor)
        let realLoss: number | undefined;
        if (targetSingleId) {
          if (isTarget) {
            const rawCandidate = data.losses?.[src.id] ?? data.losses?.[src.name] ?? data.loss ?? data.metrics?.loss ?? data.error;
            if (rawCandidate !== undefined && !isNaN(Number(rawCandidate))) {
              realLoss = Number(rawCandidate);
            }
          }
        } else {
          const rawCandidate = data.losses?.[src.id] ?? data.losses?.[src.name];
          if (rawCandidate !== undefined && !isNaN(Number(rawCandidate))) {
            realLoss = Number(rawCandidate);
          }
        }

        if (realLoss !== undefined) {
          const currentLoss = nextLoss[src.id] || nextLoss[src.name] || [];
          const pt = { time: now, value: realLoss };
          const updatedHistory = [...currentLoss, pt].slice(-30);
          nextLoss[src.id] = updatedHistory;
          nextLoss[src.name] = updatedHistory;
        }

        // 3. Resolve PSI / Drift Score (Strictly isolated per sensor)
        let realPsi: number | undefined;
        if (targetSingleId) {
          if (isTarget) {
            const rawCandidate = data.drift_scores?.[src.id] ?? data.drift_scores?.[src.name] ?? data.drift ?? data.metrics?.psi ?? data.metrics?.drift_score;
            if (rawCandidate !== undefined && !isNaN(Number(rawCandidate))) {
              realPsi = Number(rawCandidate);
            }
          }
        } else {
          const rawCandidate = data.drift_scores?.[src.id] ?? data.drift_scores?.[src.name];
          if (rawCandidate !== undefined && !isNaN(Number(rawCandidate))) {
            realPsi = Number(rawCandidate);
          }
        }

        if (realPsi !== undefined) {
          const currentDrift = nextDrift[src.id] || nextDrift[src.name] || [];
          const pt = { time: now, value: realPsi };
          const updatedHistory = [...currentDrift, pt].slice(-30);
          nextDrift[src.id] = updatedHistory;
          nextDrift[src.name] = updatedHistory;
        }

        // 4. Resolve Quality Score (Dynamic & isolated)
        let calculatedQuality = src.quality;
        if (data.qualities?.[src.id] !== undefined) {
          calculatedQuality = Number(data.qualities[src.id]);
        } else if (data.qualities?.[src.name] !== undefined) {
          calculatedQuality = Number(data.qualities[src.name]);
        } else if (realLoss !== undefined) {
          calculatedQuality = Math.min(100, Math.max(10, Math.round(100 - realLoss * 1200)));
        } else if (src.confidence_score !== undefined && src.confidence_score !== null) {
          calculatedQuality = Math.round(src.confidence_score * 100);
        }

        return {
          ...src,
          latest_value: val !== undefined ? Number(val) : src.latest_value,
          quality: calculatedQuality,
        } as DataSourceItem;
      });

      const nextEngineData: EngineDataPayload = {
        ...(state.latestEngineData || {}),
        ...data,
        edge_data: data.edge_data ?? state.latestEngineData?.edge_data,
        sensor_snapshot: data.sensor_snapshot
          ? {
              ...(state.latestEngineData?.sensor_snapshot || {}),
              ...data.sensor_snapshot,
            }
          : state.latestEngineData?.sensor_snapshot,
        mean_speed: data.mean_speed ?? state.latestEngineData?.mean_speed,
        mean_occupancy: data.mean_occupancy ?? state.latestEngineData?.mean_occupancy,
      };

      return {
        latestEngineData: nextEngineData,
        sources: updatedSources,
        lossHistory: nextLoss,
        driftHistory: nextDrift,
        fuserLossHistory: nextFuserLoss,
        fuserDriftHistory: nextFuserDrift,
      };
    });
  },
}));
