// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { useSystemStore, useSensorsStore } from '../../stores';
import { DashboardKpiCards } from './DashboardKpiCards';
import { SensorHealthTable } from './SensorHealthTable';
import { TelemetryCharts } from './TelemetryCharts';

export const LiveDashboard: React.FC = () => {
  const phase = useSystemStore((s) => s.phase);
  const latencyMs = useSystemStore((s) => s.latencyMs);
  const {
    sources,
    selectedSourceId,
    setSelectedSourceId,
    fuserLossHistory,
    fuserDriftHistory,
  } = useSensorsStore();

  const liveSensors = sources.filter(
    (s) =>
      s.source_type !== 'SUMO Network' &&
      s.id !== 'map_main' &&
      s.source_type !== 'Parquet' &&
      s.id !== 'historical_base'
  );

  const activeSource = liveSensors.find((s) => s.id === selectedSourceId) || liveSensors[0];

  const avgPsi =
    fuserDriftHistory.length > 0
      ? (fuserDriftHistory.reduce((acc, p) => acc + p.value, 0) / fuserDriftHistory.length).toFixed(3)
      : '0.000';

  return (
    <div className="h-[calc(100vh-4rem-2rem)] overflow-y-auto p-6 space-y-6 bg-background select-none">
      {/* 1. Header Summary Cards */}
      <DashboardKpiCards
        phase={phase}
        sensorCount={liveSensors.length}
        avgPsi={avgPsi}
        latencyMs={latencyMs > 0 ? latencyMs.toFixed(2) : '--'}
      />

      {/* 2. Zero-Trust Data Sources Health Table */}
      <SensorHealthTable
        sources={liveSensors}
        selectedSourceId={activeSource?.id || null}
        onSelectSource={setSelectedSourceId}
      />

      {/* 3. MLOps Live Charts: Central Fuser Agent (iTransformer + PINO) */}
      <TelemetryCharts
        modelName="Fuser Agent (iTransformer + PINO)"
        lossPoints={fuserLossHistory}
        driftPoints={fuserDriftHistory}
      />
    </div>
  );
};
