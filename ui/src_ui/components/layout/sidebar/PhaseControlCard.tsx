// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { useTranslation } from 'react-i18next';
import { Lock, Loader2 } from 'lucide-react';
import { usePhaseControl } from '../../../hooks/usePhaseControl';

interface PhaseControlCardProps {
  openImportWizard: (step?: 1 | 2 | 3) => void;
}

/**
 * Single Responsibility Principle (SRP):
 * Renders the Phase status card, status pills, and the locked/interactive lifecycle action button.
 */
export const PhaseControlCard: React.FC<PhaseControlCardProps> = ({ openImportWizard }) => {
  const { t } = useTranslation();
  const {
    phase,
    isRunningPhase,
    isStartingPhase,
    hasMap,
    hasParquet,
    hasSensors,
    isStartOptLocked,
    btnConfig,
    optLockTooltip,
    handleControlAction,
  } = usePhaseControl();

  const Icon = btnConfig.icon;

  return (
    <div className="glass-panel p-4 rounded-xl space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
          {t('controls.phase')}
        </span>
      </div>

      <div className="p-3 bg-background/80 border border-border rounded-lg space-y-2">
        <div className="flex items-center justify-between">
          <p className="text-sm font-bold text-slate-900 dark:text-white tracking-tight">
            {phase === 'IDLE_OPTIMIZATION' && t('controls.idleOptimization')}
            {phase === 'RUNNING_OPTIMIZATION' && t('controls.runningOptimization')}
            {phase === 'IDLE_OFFLINE' && t('controls.idleOffline')}
            {phase === 'RUNNING_OFFLINE' && t('controls.runningOffline')}
            {phase === 'IDLE_ONLINE' && t('controls.idleOnline')}
            {phase === 'RUNNING_ONLINE' && t('controls.runningOnline')}
          </p>
          {phase === 'IDLE_OPTIMIZATION' && isStartOptLocked && (
            <span
              title={`Pré-requisitos pendentes:\n${!hasMap ? '• Mapa SUMO\n' : ''}${!hasParquet ? '• Base Parquet\n' : ''}${!hasSensors ? '• Sensores' : ''}`}
            >
              <Lock className="w-3.5 h-3.5 text-amber-500/80" />
            </span>
          )}
          {isRunningPhase && (
            <span title="Processamento da fase em andamento...">
              <Loader2 className="w-3.5 h-3.5 text-primary-500 animate-spin" />
            </span>
          )}
        </div>

        {/* Minimalist 3-Pill Status Row for Phase 0 */}
        {phase === 'IDLE_OPTIMIZATION' && (
          <div className="flex items-center gap-1.5 pt-0.5">
            <button
              type="button"
              onClick={() => openImportWizard(1)}
              title={
                hasMap
                  ? 'Mapa SUMO carregado'
                  : 'Clique para carregar o Mapa SUMO (.net.xml / .net.xml.gz)'
              }
              className={`flex-1 py-1 px-2 rounded-lg text-[10px] font-medium border flex items-center justify-center gap-1.5 transition-all ${
                hasMap
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-600 dark:text-emerald-400'
                  : 'bg-surface/50 border-border text-slate-400 dark:text-slate-500 hover:border-slate-400 dark:hover:border-slate-600 hover:text-slate-700 dark:hover:text-slate-300'
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  hasMap ? 'bg-emerald-500' : 'bg-slate-300 dark:bg-slate-600'
                }`}
              />
              <span>Mapa</span>
            </button>

            <button
              type="button"
              onClick={() => openImportWizard(2)}
              title={
                hasParquet
                  ? 'Base Parquet importada'
                  : 'Clique para importar a base Parquet (.parquet)'
              }
              className={`flex-1 py-1 px-2 rounded-lg text-[10px] font-medium border flex items-center justify-center gap-1.5 transition-all ${
                hasParquet
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-600 dark:text-emerald-400'
                  : 'bg-surface/50 border-border text-slate-400 dark:text-slate-500 hover:border-slate-400 dark:hover:border-slate-600 hover:text-slate-700 dark:hover:text-slate-300'
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  hasParquet ? 'bg-emerald-500' : 'bg-slate-300 dark:bg-slate-600'
                }`}
              />
              <span>Parquet</span>
            </button>

            <button
              type="button"
              onClick={() => openImportWizard(3)}
              title={hasSensors ? 'Sensores cadastrados' : 'Clique para cadastrar Sensores'}
              className={`flex-1 py-1 px-2 rounded-lg text-[10px] font-medium border flex items-center justify-center gap-1.5 transition-all ${
                hasSensors
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-600 dark:text-emerald-400'
                  : 'bg-surface/50 border-border text-slate-400 dark:text-slate-500 hover:border-slate-400 dark:hover:border-slate-600 hover:text-slate-700 dark:hover:text-slate-300'
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  hasSensors ? 'bg-emerald-500' : 'bg-slate-300 dark:bg-slate-600'
                }`}
              />
              <span>Sensores</span>
            </button>
          </div>
        )}
      </div>

      <button
        type="button"
        onClick={handleControlAction}
        disabled={btnConfig.disabled}
        title={
          isStartOptLocked
            ? optLockTooltip
            : isRunningPhase || isStartingPhase
            ? 'Processamento da fase em andamento...'
            : undefined
        }
        className={`w-full py-3 px-4 rounded-xl text-xs font-bold flex items-center justify-center gap-2 shadow-lg transition-all transform ${
          btnConfig.disabled ? 'cursor-not-allowed' : 'active:scale-95'
        } ${btnConfig.color} ${btnConfig.active ? 'animate-pulse' : ''}`}
      >
        <Icon
          className={`w-4 h-4 ${
            isRunningPhase || isStartingPhase ? 'animate-spin' : ''
          }`}
        />
        {btnConfig.label}
      </button>
    </div>
  );
};
