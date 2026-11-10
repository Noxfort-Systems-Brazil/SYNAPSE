// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React, { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import ReactECharts from 'echarts-for-react';
import { ShieldAlert, TrendingUp } from 'lucide-react';
import { TelemetryPoint } from '../../types/sensors';
import { createMseLossChartOption, createDriftPsiChartOption } from '../../utils/chartOptions';
import { useSystemStore } from '../../stores';

interface TelemetryChartsProps {
  modelName?: string;
  sensorName?: string;
  lossPoints: TelemetryPoint[];
  driftPoints: TelemetryPoint[];
}

export const TelemetryCharts: React.FC<TelemetryChartsProps> = ({
  modelName,
  sensorName,
  lossPoints,
  driftPoints,
}) => {
  const { t } = useTranslation();
  const theme = useSystemStore((s) => s.theme);
  const phase = useSystemStore((s) => s.phase);
  const isDark = theme === 'dark';
  const isOnline = phase === 'RUNNING_ONLINE';
  const activeAgent = modelName || (sensorName ? sensorName : 'Fuser Agent (iTransformer + PINO)');

  const lossChartOption = useMemo(() => createMseLossChartOption(lossPoints, isDark), [lossPoints, isDark]);
  const driftChartOption = useMemo(() => createDriftPsiChartOption(driftPoints, isDark), [driftPoints, isDark]);

  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
      <div className="glass-panel p-6 rounded-2xl space-y-2 relative overflow-hidden">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-bold text-slate-800 dark:text-white uppercase tracking-wider flex items-center gap-1.5">
            <ShieldAlert className="w-4 h-4 text-rose-500 dark:text-rose-400" />
            {t('dashboard.reconErrorGlobal')}
          </h4>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
              {t('dashboard.agentLabel')} <b className="text-rose-600 dark:text-rose-300">{activeAgent}</b>
            </span>
            <span className={`px-2 py-0.5 rounded text-[9px] font-bold font-mono ${lossPoints.length > 0 ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30' : 'bg-slate-200 dark:bg-slate-800 text-slate-500 dark:text-slate-400'}`}>
              {lossPoints.length > 0 ? `${lossPoints.length} pts` : isOnline ? t('status.receiving') : t('status.standby')}
            </span>
          </div>
        </div>
        <div className="h-56 w-full relative">
          <ReactECharts option={lossChartOption} style={{ height: '100%', width: '100%' }} notMerge={true} lazyUpdate={true} />
        </div>
      </div>

      <div className="glass-panel p-6 rounded-2xl space-y-2 relative overflow-hidden">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-bold text-slate-800 dark:text-white uppercase tracking-wider flex items-center gap-1.5">
            <TrendingUp className="w-4 h-4 text-primary-500 dark:text-primary-400" />
            {t('dashboard.temporalDriftPsi')}
          </h4>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
              {t('dashboard.agentLabel')} <b className="text-primary-600 dark:text-primary-300">{activeAgent}</b>
            </span>
            <span className={`px-2 py-0.5 rounded text-[9px] font-bold font-mono ${driftPoints.length > 0 ? 'bg-primary-500/15 text-primary-600 dark:text-primary-400 border border-primary-500/30' : 'bg-slate-200 dark:bg-slate-800 text-slate-500 dark:text-slate-400'}`}>
              {driftPoints.length > 0 ? `${driftPoints.length} pts` : isOnline ? t('status.receiving') : t('status.standby')}
            </span>
          </div>
        </div>
        <div className="h-56 w-full relative">
          <ReactECharts option={driftChartOption} style={{ height: '100%', width: '100%' }} notMerge={true} lazyUpdate={true} />
        </div>
      </div>
    </div>
  );
};

