// SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
// Copyright (C) 2026 Noxfort Systems
//
// File: ui/src_ui/components/settings/tabs/duckdns/DuckDnsCaddyCard.tsx
// Description: Presentational card for Caddy SSL proxy toggle switch.

import React from 'react';
import { ShieldCheck } from 'lucide-react';

interface DuckDnsCaddyCardProps {
  caddyEnabled: boolean;
  setCaddyEnabled: (val: boolean) => void;
}

export const DuckDnsCaddyCard: React.FC<DuckDnsCaddyCardProps> = ({
  caddyEnabled,
  setCaddyEnabled,
}) => {
  return (
    <div className="p-3 bg-slate-50/50 dark:bg-background/50 border border-border/80 rounded-xl flex items-center justify-between">
      <div className="flex items-center gap-2.5">
        <ShieldCheck className="w-4 h-4 text-primary-500" />
        <div>
          <span className="font-semibold text-slate-800 dark:text-slate-200 block text-[11px]">
            Proxy Reverso Caddy (Certificado SSL / HTTPS Automático)
          </span>
          <span className="text-[10px] text-slate-500 dark:text-slate-400">
            Elimina a necessidade da porta :8081 nas URLs públicas.
          </span>
        </div>
      </div>
      <label className="relative inline-flex items-center cursor-pointer">
        <input
          type="checkbox"
          checked={caddyEnabled}
          onChange={(e) => setCaddyEnabled(e.target.checked)}
          className="sr-only peer"
        />
        <div className="w-9 h-5 bg-slate-300 peer-focus:outline-none rounded-full peer dark:bg-slate-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all dark:border-slate-600 peer-checked:bg-primary-600"></div>
      </label>
    </div>
  );
};
