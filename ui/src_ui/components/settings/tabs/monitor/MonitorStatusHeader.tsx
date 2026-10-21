// SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
// Copyright (C) 2026 Noxfort Systems
//
// File: ui/src_ui/components/settings/tabs/monitor/MonitorStatusHeader.tsx
// Author: Gabriel Moraes
// Date: 2026-09-14

import React from 'react';
import { Radio } from 'lucide-react';

interface MonitorStatusHeaderProps {
  isConnected: boolean;
  protocol: string;
  isHttp: boolean;
}

export const MonitorStatusHeader: React.FC<MonitorStatusHeaderProps> = ({
  isConnected,
  protocol,
  isHttp,
}) => {
  return (
    <div className="flex items-center justify-between pb-2 border-b border-border/70">
      <div className="flex items-center gap-2">
        <Radio className="w-4 h-4 text-primary-500" />
        <span className="font-semibold text-slate-800 dark:text-slate-200">Status da Telemetria:</span>
        {isConnected ? (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 dark:bg-emerald-950/80 text-emerald-700 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-700/60 shadow-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Conectado ({protocol})
          </span>
        ) : (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-border">
            <span className="w-2 h-2 rounded-full bg-slate-400" />
            Desconectado
          </span>
        )}
      </div>

      {/* Protocol badge */}
      <span className="px-2 py-0.5 rounded-md text-[10px] font-mono font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-border/60">
        Modo: {isHttp ? '🌐 HTTP REST / Webhook' : '📡 MQTT Broker'}
      </span>
    </div>
  );
};
