// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Play, Sparkles, Radio, Lock, Loader2, LucideIcon } from 'lucide-react';
import { useSystemStore, useSensorsStore, useTopologyStore, useSecurityStore, useEtlStore } from '../stores';
import { systemService } from '../services/api';
import { SystemPhase } from '../types/system';

export interface PhaseButtonConfig {
  label: string;
  icon: LucideIcon;
  color: string;
  active: boolean;
  disabled: boolean;
}

export interface UsePhaseControlReturn {
  phase: SystemPhase;
  isRunningPhase: boolean;
  isStartingPhase: boolean;
  hasMap: boolean;
  hasParquet: boolean;
  hasSensors: boolean;
  isStartOptLocked: boolean;
  btnConfig: PhaseButtonConfig;
  optLockTooltip?: string;
  handleControlAction: () => Promise<void>;
}

/**
 * Single Responsibility Principle (SRP) & Dependency Inversion (DIP):
 * Encapsulates the ADAGIO™ lifecycle state machine, prerequisite validations,
 * authentication guard, and IPC transitions for all system phases.
 */
export const usePhaseControl = (): UsePhaseControlReturn => {
  const { t } = useTranslation();
  const phase = useSystemStore((s) => s.phase);
  const setPhase = useSystemStore((s) => s.setPhase);
  const addLog = useSystemStore((s) => s.addLog);
  const sources = useSensorsStore((s) => s.sources);
  const mapLoaded = useTopologyStore((s) => s.mapLoaded || s.nodes.length > 0);
  const importProgress = useEtlStore((s) => s.importProgress);
  const hasDataset = useEtlStore((s) => s.hasDataset);
  const requestAuth = useSecurityStore((s) => s.requestAuth);

  const [isStartingPhase, setIsStartingPhase] = useState(false);

  // Live IoT sensors (excluding map elements and parquet historical dataset)
  const liveSensors = sources.filter(
    (s) =>
      s.source_type !== 'SUMO Network' &&
      s.id !== 'map_main' &&
      s.source_type !== 'Parquet' &&
      s.id !== 'historical_base'
  );

  // Prerequisites for starting Phase 0 (Optimization): Map, Parquet, and Sensors
  const hasMap = mapLoaded;
  const hasParquet = importProgress.progress === 100 || hasDataset;
  const hasSensors = liveSensors.length > 0;

  const isOptPrerequisitesMet = hasMap && hasParquet && hasSensors;
  const isStartOptLocked = phase === 'IDLE_OPTIMIZATION' && !isOptPrerequisitesMet;
  const isRunningPhase =
    phase === 'RUNNING_OPTIMIZATION' ||
    phase === 'RUNNING_OFFLINE' ||
    phase === 'RUNNING_ONLINE';

  const handleControlAction = async () => {
    if (isStartOptLocked || isRunningPhase || isStartingPhase) return;

    const executeAction = async () => {
      switch (phase) {
        case 'IDLE_OPTIMIZATION':
          setIsStartingPhase(true);
          setPhase('RUNNING_OPTIMIZATION');
          try {
            await systemService.startOptimization();
          } catch (err: any) {
            console.error('[usePhaseControl] Erro ao iniciar otimização:', err);
            setPhase('IDLE_OPTIMIZATION');
            addLog('ERROR', `Erro ao iniciar otimização: ${err?.message || err}`);
          } finally {
            setIsStartingPhase(false);
          }
          break;

        case 'IDLE_OFFLINE':
          setIsStartingPhase(true);
          setPhase('RUNNING_OFFLINE');
          try {
            await systemService.startOfflineBootstrap();
          } catch (err: any) {
            console.error('[usePhaseControl] Erro ao iniciar bootstrap:', err);
            setPhase('IDLE_OFFLINE');
            addLog('ERROR', `Erro ao iniciar bootstrap: ${err?.message || err}`);
          } finally {
            setIsStartingPhase(false);
          }
          break;

        case 'IDLE_ONLINE':
          setIsStartingPhase(true);
          setPhase('RUNNING_ONLINE');
          try {
            await systemService.startOnlineOperation();
          } catch (err: any) {
            console.error('[usePhaseControl] Erro ao iniciar operação online:', err);
            setPhase('IDLE_ONLINE');
            addLog('ERROR', `Erro ao iniciar operação online: ${err?.message || err}`);
          } finally {
            setIsStartingPhase(false);
          }
          break;
      }
    };

    // Sensitive control actions are guarded by the Security Layer
    requestAuth(executeAction);
  };

  const getOptLockTooltip = () => {
    if (!isStartOptLocked) return undefined;
    const missing: string[] = [];
    if (!hasMap) missing.push('Mapa');
    if (!hasParquet) missing.push('Parquet');
    if (!hasSensors) missing.push('Sensores');
    return `Pendente: ${missing.join(', ')}`;
  };

  const getButtonConfig = (currentPhase: SystemPhase): PhaseButtonConfig => {
    switch (currentPhase) {
      case 'IDLE_OPTIMIZATION': {
        const isLocked = isStartOptLocked || isStartingPhase;
        return {
          label: isStartingPhase ? t('controls.runningOptimization') : t('controls.btnStartOpt'),
          icon: isStartingPhase ? Loader2 : isStartOptLocked ? Lock : Play,
          color: isLocked
            ? 'bg-slate-200 dark:bg-surface border border-border text-slate-400 dark:text-slate-500 cursor-not-allowed opacity-60 shadow-none'
            : 'bg-primary-600 hover:bg-primary-500 shadow-primary-600/20 text-white',
          active: false,
          disabled: isLocked,
        };
      }
      case 'RUNNING_OPTIMIZATION':
        return {
          label: t('controls.runningOptimization'),
          icon: Loader2,
          color: 'bg-slate-200 dark:bg-surface border border-border text-slate-400 dark:text-slate-500 cursor-not-allowed opacity-60 shadow-none',
          active: false,
          disabled: true,
        };
      case 'IDLE_OFFLINE': {
        const isLocked = isStartingPhase;
        return {
          label: isStartingPhase ? t('controls.runningOffline') : t('controls.btnStartOffline'),
          icon: isStartingPhase ? Loader2 : Sparkles,
          color: isLocked
            ? 'bg-slate-200 dark:bg-surface border border-border text-slate-400 dark:text-slate-500 cursor-not-allowed opacity-60 shadow-none'
            : 'bg-accent-cyan hover:bg-accent-cyan/90 text-slate-900 shadow-cyan-500/20',
          active: false,
          disabled: isLocked,
        };
      }
      case 'RUNNING_OFFLINE':
        return {
          label: t('controls.runningOffline'),
          icon: Loader2,
          color: 'bg-slate-200 dark:bg-surface border border-border text-slate-400 dark:text-slate-500 cursor-not-allowed opacity-60 shadow-none',
          active: false,
          disabled: true,
        };
      case 'IDLE_ONLINE': {
        const isLocked = isStartingPhase;
        return {
          label: isStartingPhase ? t('controls.runningOnline') : t('controls.btnStartOnline'),
          icon: isStartingPhase ? Loader2 : Radio,
          color: isLocked
            ? 'bg-slate-200 dark:bg-surface border border-border text-slate-400 dark:text-slate-500 cursor-not-allowed opacity-60 shadow-none'
            : 'bg-emerald-600 hover:bg-emerald-500 shadow-emerald-600/20 text-white',
          active: false,
          disabled: isLocked,
        };
      }
      case 'RUNNING_ONLINE':
        return {
          label: t('controls.runningOnline'),
          icon: Loader2,
          color: 'bg-slate-200 dark:bg-surface border border-border text-slate-400 dark:text-slate-500 cursor-not-allowed opacity-60 shadow-none',
          active: false,
          disabled: true,
        };
      default:
        return {
          label: t('controls.btnStartOpt'),
          icon: Play,
          color: 'bg-primary-600 hover:bg-primary-500 shadow-primary-600/20 text-white',
          active: false,
          disabled: false,
        };
    }
  };

  return {
    phase,
    isRunningPhase,
    isStartingPhase,
    hasMap,
    hasParquet,
    hasSensors,
    isStartOptLocked,
    btnConfig: getButtonConfig(phase),
    optLockTooltip: getOptLockTooltip(),
    handleControlAction,
  };
};
