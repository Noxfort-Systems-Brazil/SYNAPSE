// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { useTranslation } from 'react-i18next';
import { ShieldCheck } from 'lucide-react';
import { useSystemStore, useTopologyStore, useSensorsStore } from '../../stores';

import { isTauriEnvironment } from '../../services/transport';

export const StatusBar: React.FC = () => {
  const { t } = useTranslation();
  const connected = useSystemStore((s) => s.connected);
  const isNative = isTauriEnvironment();
  const nodesCount = useTopologyStore((s) => s.nodes.length);
  const edgesCount = useTopologyStore((s) => s.edges.length);
  const latestEngineData = useSensorsStore((s) => s.latestEngineData);

  const getStatusText = () => {
    if (!isNative) return 'WEB BROWSER (SEM BRIDGE NATIVA)';
    return connected ? 'IPC PIPE: CONNECTED' : 'IPC PIPE: DISCONNECTED';
  };

  return (
    <footer className="h-8 border-t border-border bg-surface/90 backdrop-blur-md px-3 sm:px-4 flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 font-mono select-none z-30 overflow-hidden whitespace-nowrap">
      {/* Left items */}
      <div className="flex items-center gap-2 sm:gap-4 shrink-0 min-w-0">
        <div className="flex items-center gap-1.5 shrink-0" title={!isNative ? 'Para conectar ao backend Python via IPC, use a janela Desktop nativa executando python synapse.py' : ''}>
          <span className={`w-2 h-2 rounded-full shrink-0 ${connected ? 'bg-emerald-400' : isNative ? 'bg-rose-500 animate-ping' : 'bg-amber-500'}`} />
          <span className={`font-semibold shrink-0 ${connected ? 'text-emerald-500 dark:text-emerald-400' : isNative ? 'text-rose-500 dark:text-rose-400' : 'text-amber-500 dark:text-amber-400'}`}>
            {getStatusText()}
          </span>
        </div>

        <span className="hidden sm:inline text-slate-300 dark:text-slate-600">|</span>

        <div className="hidden sm:block shrink-0">
          <span>{t('map.nodesCount')}: </span>
          <span className="text-slate-800 dark:text-slate-200 font-bold">{nodesCount}</span>
          <span className="ml-2">{t('map.edgesCount')}: </span>
          <span className="text-slate-800 dark:text-slate-200 font-bold">{edgesCount}</span>
        </div>
      </div>

      {/* Right items */}
      <div className="flex items-center gap-2 sm:gap-4 shrink-0">
        {latestEngineData && (
          <>
            <div className="hidden md:block shrink-0">
              <span>{t('metrics.meanSpeed')}: </span>
              <span className="text-accent-cyan font-bold">
                {latestEngineData.mean_speed ? `${latestEngineData.mean_speed.toFixed(1)} km/h` : '--'}
              </span>
            </div>
            <span className="hidden md:inline text-slate-300 dark:text-slate-600">|</span>
          </>
        )}

        <div className="flex items-center gap-1.5 text-primary-600 dark:text-primary-400 font-bold shrink-0">
          <ShieldCheck className="w-3.5 h-3.5 shrink-0" />
          <span className="hidden md:inline">ZERO-TRUST MEMORY</span>
        </div>
      </div>
    </footer>
  );
};
