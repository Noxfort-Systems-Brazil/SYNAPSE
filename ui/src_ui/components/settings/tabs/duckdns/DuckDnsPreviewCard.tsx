// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { Activity, ShieldCheck, Check, Copy } from 'lucide-react';

interface DuckDnsPreviewCardProps {
  previewUrl: string;
  copied: boolean;
  onCopy: (url: string) => void;
}

export const DuckDnsPreviewCard: React.FC<DuckDnsPreviewCardProps> = ({
  previewUrl,
  copied,
  onCopy,
}) => {
  if (!previewUrl) return null;

  return (
    <div className="p-4 bg-gradient-to-br from-primary-950/20 to-slate-900/40 border border-primary-500/30 rounded-xl space-y-2">
      <div className="flex items-center justify-between">
        <span className="font-bold text-slate-800 dark:text-slate-100 flex items-center gap-1.5 text-[11px]">
          <Activity className="w-3.5 h-3.5 text-accent-cyan" />
          URL Unificada de Ingestão de Câmeras (Street / 4G / Local):
        </span>
        <span className="text-[10px] text-emerald-500 font-semibold flex items-center gap-1">
          <ShieldCheck className="w-3 h-3" /> HTTPS Seguro
        </span>
      </div>

      <div className="flex items-center gap-2">
        <input
          type="text"
          readOnly
          value={previewUrl}
          className="w-full h-8 px-2.5 bg-surface dark:bg-background border border-border rounded-lg text-accent-cyan font-mono text-xs font-semibold select-all"
        />
        <button
          type="button"
          onClick={() => onCopy(previewUrl)}
          className="px-2.5 h-8 bg-surface dark:bg-background border border-border hover:border-slate-400 dark:hover:border-slate-600 rounded-lg text-slate-700 dark:text-slate-300 flex items-center gap-1 font-semibold transition-colors cursor-pointer"
          title="Copiar URL"
        >
          {copied ? (
            <Check className="w-3.5 h-3.5 text-emerald-500" />
          ) : (
            <Copy className="w-3.5 h-3.5" />
          )}
        </button>
      </div>
      <p className="text-[10px] text-slate-400 leading-relaxed">
        Todas as fontes remotas (câmeras nas ruas ou simuladores) enviam dados adicionando o ID do sensor ao final:
        <code className="ml-1 px-1 py-0.5 bg-slate-800 rounded text-accent-cyan font-mono">
          {previewUrl}/src_1
        </code>
      </p>
    </div>
  );
};
