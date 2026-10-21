// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';

interface MapTrafficLegendProps {
  visible: boolean;
}

export const MapTrafficLegend: React.FC<MapTrafficLegendProps> = ({ visible }) => {
  if (!visible) return null;

  return (
    <div className="absolute bottom-4 right-4 z-10 glass-panel px-3 py-2 rounded-xl border border-border/70 bg-surface/90 text-[10px] font-mono space-y-1 select-none shadow-xl">
      <div className="text-[9px] uppercase tracking-wider font-sans font-bold text-slate-400">
        Regime Fluidodinâmico
      </div>
      <div className="flex items-center gap-3 text-[10px]">
        <div className="flex items-center gap-1 text-slate-700 dark:text-slate-300">
          <span className="w-2 h-2 rounded-full bg-slate-900 dark:bg-slate-400" />
          <span>&gt; 45 km/h</span>
        </div>
        <div className="flex items-center gap-1 text-amber-500 dark:text-amber-400">
          <span className="w-2 h-2 rounded-full bg-amber-500" />
          <span>20–45 km/h</span>
        </div>
        <div className="flex items-center gap-1 text-rose-500 dark:text-rose-400">
          <span className="w-2 h-2 rounded-full bg-rose-500" />
          <span>&lt; 20 km/h</span>
        </div>
        <div className="flex items-center gap-1 text-accent-cyan">
          <span className="w-2 h-2 rounded-full bg-accent-cyan" />
          <span>Sensor</span>
        </div>
      </div>
    </div>
  );
};
