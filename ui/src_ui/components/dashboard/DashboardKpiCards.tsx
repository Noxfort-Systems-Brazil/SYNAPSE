// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { useTranslation } from 'react-i18next';
import { Activity, Radio, TrendingUp, Clock } from 'lucide-react';
import { SystemPhase } from '../../types/system';

interface DashboardKpiCardsProps {
  phase: SystemPhase;
  sensorCount: number;
  avgPsi: string;
  latencyMs?: string;
}

export const DashboardKpiCards: React.FC<DashboardKpiCardsProps> = ({
  phase,
  sensorCount,
  avgPsi,
  latencyMs = '1.42',
}) => {
  const { t } = useTranslation();

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
      {/* Card 1: System Status */}
      <div className="glass-panel p-5 rounded-2xl relative overflow-hidden group">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            {t('metrics.throughput')}
          </span>
          <div className="p-2 rounded-xl bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
            <Activity className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3 flex items-center gap-2">
          <span
            className={`w-2.5 h-2.5 rounded-full ${
              phase === 'RUNNING_ONLINE' ? 'bg-emerald-500 animate-ping' : 'bg-slate-400 dark:bg-slate-500'
            }`}
          />
          <span className="text-lg font-black text-slate-900 dark:text-white tracking-tight">
            {phase === 'RUNNING_ONLINE'
              ? t('status.onlineHft')
              : phase === 'RUNNING_OFFLINE'
              ? t('status.bootstrap')
              : t('status.standby')}
          </span>
        </div>
      </div>

      {/* Card 2: Active Sources */}
      <div className="glass-panel p-5 rounded-2xl relative overflow-hidden group">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            {t('metrics.activeSensors')}
          </span>
          <div className="p-2 rounded-xl bg-primary-50 dark:bg-primary-500/10 text-primary-600 dark:text-primary-400">
            <Radio className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">{sensorCount}</span>
          <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">
            {t('dashboard.monitoredSensors')}
          </span>
        </div>
      </div>

      {/* Card 3: Avg PSI Score (Drift) */}
      <div className="glass-panel p-5 rounded-2xl relative overflow-hidden group">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            {t('metrics.driftScore')}
          </span>
          <div className="p-2 rounded-xl bg-amber-50 dark:bg-amber-500/10 text-amber-600 dark:text-amber-400">
            <TrendingUp className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">{avgPsi}</span>
          <span className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">
            {t('dashboard.stable')} (&lt; 0.10)
          </span>
        </div>
      </div>

      {/* Card 4: Avg Latency */}
      <div className="glass-panel p-5 rounded-2xl relative overflow-hidden group">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            {t('dashboard.cycleLatency')}
          </span>
          <div className="p-2 rounded-xl bg-accent-cyan/10 text-accent-cyan">
            <Clock className="w-4 h-4" />
          </div>
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-2xl font-black text-slate-900 dark:text-white tracking-tight">{latencyMs}</span>
          <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">ms (HFT Link)</span>
        </div>
      </div>
    </div>
  );
};

