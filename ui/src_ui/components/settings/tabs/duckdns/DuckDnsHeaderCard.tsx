// SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
// Copyright (C) 2026 Noxfort Systems
//
// File: ui/src_ui/components/settings/tabs/duckdns/DuckDnsHeaderCard.tsx
// Description: Presentational header card displaying connection status and toggle.

import React from 'react';
import { Globe, Loader2, Power } from 'lucide-react';

interface DuckDnsHeaderCardProps {
  isOnline: boolean;
  enabled: boolean;
  saving: boolean;
  canConnect: boolean;
  onToggle: () => void;
}

export const DuckDnsHeaderCard: React.FC<DuckDnsHeaderCardProps> = ({
  isOnline,
  enabled,
  saving,
  canConnect,
  onToggle,
}) => {
  return (
    <div className="p-4 bg-slate-50 dark:bg-background/80 border border-border rounded-xl flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div
          className={`w-9 h-9 rounded-xl flex items-center justify-center ${
            isOnline
              ? 'bg-emerald-500/10 text-emerald-500'
              : 'bg-slate-500/10 text-slate-400'
          }`}
        >
          <Globe className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-slate-900 dark:text-white">
              Acesso Remoto via DuckDNS (Dynamic DNS)
            </span>
            <span
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${
                isOnline
                  ? 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30'
                  : 'bg-slate-500/15 text-slate-600 dark:text-slate-400 border border-slate-500/30'
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  isOnline ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'
                }`}
              />
              {isOnline ? 'ONLINE' : 'DESCONECTADO'}
            </span>
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
            Conexão resiliente para Prefeituras: sobrevive a quedas de energia e trocas de IP da operadora.
          </p>
        </div>
      </div>

      <button
        onClick={onToggle}
        disabled={saving || (!enabled && !canConnect)}
        className={`px-3 py-1.5 rounded-xl font-bold flex items-center gap-1.5 shadow-sm transition-all cursor-pointer active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed ${
          isOnline
            ? 'bg-rose-600 hover:bg-rose-500 text-white'
            : 'bg-emerald-600 hover:bg-emerald-500 text-white'
        }`}
      >
        {saving ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin" />
        ) : (
          <Power className="w-3.5 h-3.5" />
        )}
        <span>{isOnline ? 'Desconectar' : 'Conectar'}</span>
      </button>
    </div>
  );
};
