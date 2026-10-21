// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { History, Activity } from 'lucide-react';
import { XaiAuditVerdict, XaiResultItem } from '../../types/xai';

interface XaiHistoryPanelProps {
  latestVerdict: XaiAuditVerdict;
  xaiHistory: XaiResultItem[];
  selectedResultId: string;
  onSelectResult: (id: string | null) => void;
  onOpenReport?: () => void;
}

export const XaiHistoryPanel: React.FC<XaiHistoryPanelProps> = ({
  latestVerdict,
  xaiHistory,
  selectedResultId,
  onSelectResult,
}) => {
  return (
    <div className="glass-panel p-4 rounded-2xl space-y-3 flex flex-col h-[560px]">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-border/80 pb-2">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-800 dark:text-slate-200">
          <History className="w-3.5 h-3.5 text-primary-500" />
          <span>Auditoria em Tempo Real</span>
        </div>
        <span className="text-[10px] font-mono text-slate-400">
          {xaiHistory.length} eventos
        </span>
      </div>

      {/* Content Area: Real-Time Audit Stream */}
      <div className="space-y-2 flex-1 overflow-y-auto pr-1">
        {/* Pending Vetos / Zero-Trust Buffer Root */}
        <div
          onClick={() => onSelectResult(null)}
          className="p-3 rounded-xl bg-background/80 border border-border hover:border-slate-400 dark:hover:border-slate-600 cursor-pointer transition-all"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-primary-400" />
              <span>Zero-Trust Buffer</span>
            </span>
            <span
              className={`w-2 h-2 rounded-full ${
                latestVerdict.safe ? 'bg-emerald-500 dark:bg-emerald-400' : 'bg-rose-500'
              }`}
            />
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            Status: {latestVerdict.safe ? 'Consistência Aprovada' : 'Anomalia Vetada'}
          </p>
        </div>

        {/* Previous Inference Requests */}
        {xaiHistory.length === 0 ? (
          <div className="p-4 rounded-xl border border-dashed border-border/80 text-center text-[11px] text-slate-400 dark:text-slate-500">
            Nenhuma análise recente. Execute uma inferência para registrar.
          </div>
        ) : (
          xaiHistory.map((item) => (
            <div
              key={item.id}
              onClick={() => onSelectResult(item.id)}
              className={`p-3 rounded-xl border cursor-pointer transition-all ${
                selectedResultId === item.id
                  ? 'bg-primary-600/20 border-primary-500/50 text-primary-900 dark:text-white font-bold'
                  : 'bg-background/80 border-border hover:border-slate-400 dark:hover:border-slate-700 text-slate-700 dark:text-slate-300'
              }`}
            >
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold truncate">{item.target}</span>
                <span className="font-mono text-[10px] text-slate-400 dark:text-slate-500">
                  {item.timestamp}
                </span>
              </div>
              <div className="text-[11px] text-accent-cyan mt-1 font-mono">
                Δ: {item.convergence_delta.toFixed(4)}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
