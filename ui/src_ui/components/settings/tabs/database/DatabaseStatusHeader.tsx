// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { Database } from 'lucide-react';

interface DatabaseStatusHeaderProps {
  isConnected: boolean;
}

export const DatabaseStatusHeader: React.FC<DatabaseStatusHeaderProps> = ({ isConnected }) => {
  return (
    <div className="flex items-center justify-between pb-2 border-b border-border/70">
      <div className="flex items-center gap-2">
        <Database className="w-4 h-4 text-primary-500" />
        <span className="font-semibold text-slate-800 dark:text-slate-200">Status do PostgreSQL:</span>
        {isConnected ? (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-100 dark:bg-emerald-950/80 text-emerald-700 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-700/60 shadow-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            Conectado
          </span>
        ) : (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-border">
            <span className="w-2 h-2 rounded-full bg-slate-400" />
            Desconectado
          </span>
        )}
      </div>
    </div>
  );
};
