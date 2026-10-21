// SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
// Copyright (C) 2026 Noxfort Systems
//
// File: ui/src_ui/components/settings/tabs/monitor/MonitorActionButtons.tsx
// Author: Gabriel Moraes
// Date: 2026-09-14

import React from 'react';
import { CheckCircle2, Wifi, WifiOff } from 'lucide-react';

interface MonitorActionButtonsProps {
  isConnected: boolean;
  testing: boolean;
  feedback: { ok: boolean; msg: string } | null;
  onConnect: () => void;
  onDisconnect: () => void;
}

export const MonitorActionButtons: React.FC<MonitorActionButtonsProps> = ({
  isConnected,
  testing,
  feedback,
  onConnect,
  onDisconnect,
}) => {
  return (
    <>
      {/* Feedback alert */}
      {feedback && (
        <div
          className={`p-3 rounded-xl flex items-center gap-2 border ${
            feedback.ok
              ? 'bg-emerald-50 dark:bg-emerald-950/60 border-emerald-200 dark:border-emerald-500/40 text-emerald-800 dark:text-emerald-300'
              : 'bg-rose-50 dark:bg-rose-950/60 border-rose-200 dark:border-rose-500/40 text-rose-700 dark:text-rose-300'
          }`}
        >
          {feedback.ok ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
          ) : (
            <WifiOff className="w-4 h-4 text-rose-600 dark:text-rose-400 shrink-0" />
          )}
          <span className="leading-tight">{feedback.msg}</span>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center pt-2 border-t border-border/80">
        {isConnected ? (
          <button
            onClick={onDisconnect}
            disabled={testing}
            className="px-4 py-2 rounded-xl font-semibold flex items-center gap-2 transition-all bg-rose-50 dark:bg-rose-950/40 border border-rose-300 dark:border-rose-700/60 text-rose-700 dark:text-rose-300 hover:bg-rose-100 dark:hover:bg-rose-900/60 shadow-xs cursor-pointer"
          >
            <WifiOff className="w-4 h-4 text-rose-500" />
            Desconectar Telemetria
          </button>
        ) : (
          <button
            onClick={onConnect}
            disabled={testing}
            className="px-4 py-2 bg-primary-600 hover:bg-primary-500 text-white rounded-xl font-bold shadow-md shadow-primary-600/20 flex items-center gap-2 transition-all cursor-pointer"
          >
            {testing ? (
              <span className="flex items-center gap-2">
                <span className="w-3 h-3 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                Testando Conexão...
              </span>
            ) : (
              <>
                <Wifi className="w-4 h-4" />
                Conectar Telemetria
              </>
            )}
          </button>
        )}
      </div>
    </>
  );
};
