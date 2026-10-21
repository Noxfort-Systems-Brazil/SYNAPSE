// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { useSystemStore } from '../../../stores';

export interface PhaseBadgeConfig {
  label: string;
  badgeClass: string;
  dotClass: string;
}

export const DEFAULT_PHASE_CONFIGS: Record<string, PhaseBadgeConfig> = {
  RUNNING_ONLINE: {
    label: 'ONLINE HFT',
    badgeClass: 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/60 border-emerald-300 dark:border-emerald-500/30 animate-pulse font-semibold',
    dotClass: 'bg-emerald-500 dark:bg-emerald-400',
  },
  RUNNING_OPTIMIZATION: {
    label: 'COMPUTING',
    badgeClass: 'text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/60 border-amber-300 dark:border-amber-500/30 animate-pulse font-semibold',
    dotClass: 'bg-amber-500 dark:bg-amber-400',
  },
  RUNNING_OFFLINE: {
    label: 'COMPUTING',
    badgeClass: 'text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/60 border-amber-300 dark:border-amber-500/30 animate-pulse font-semibold',
    dotClass: 'bg-amber-500 dark:bg-amber-400',
  },
};

export const IDLE_PHASE_CONFIG: PhaseBadgeConfig = {
  label: 'IDLE',
  badgeClass: 'text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-900 border-slate-200 dark:border-slate-800 font-medium',
  dotClass: 'bg-slate-400 dark:bg-slate-500',
};

interface HeaderPhaseBadgeProps {
  phase?: string;
  configs?: Record<string, PhaseBadgeConfig>;
}

/**
 * Atomic subcomponent for displaying the active system phase (SRP + OCP).
 */
export const HeaderPhaseBadge: React.FC<HeaderPhaseBadgeProps> = ({
  phase: propPhase,
  configs = DEFAULT_PHASE_CONFIGS,
}) => {
  const storePhase = useSystemStore((s) => s.phase);
  const activePhase = propPhase !== undefined ? propPhase : storePhase;

  const currentConfig = configs[activePhase] || IDLE_PHASE_CONFIG;

  return (
    <span
      title={`Status do Sistema: ${currentConfig.label}`}
      className={`flex items-center gap-1.5 px-2.5 sm:px-3 py-1 text-xs border rounded-full shrink-0 whitespace-nowrap ${currentConfig.badgeClass}`}
    >
      <span className={`w-2 h-2 rounded-full shrink-0 ${currentConfig.dotClass}`} />
      <span className="hidden sm:inline whitespace-nowrap">{currentConfig.label}</span>
    </span>
  );
};
