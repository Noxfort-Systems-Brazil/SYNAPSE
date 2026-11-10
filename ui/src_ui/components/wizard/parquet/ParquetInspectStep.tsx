// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';

interface ParquetInspectionData {
  num_rows: number;
  size_mb: number;
  columns: string[];
}

interface ParquetInspectStepProps {
  parquetInspection: ParquetInspectionData;
}

export const ParquetInspectStep: React.FC<ParquetInspectStepProps> = ({
  parquetInspection,
}) => {
  return (
    <div className="space-y-4 text-xs font-mono">
      <div className="grid grid-cols-3 gap-3">
        <div className="p-3 rounded-xl bg-surface dark:bg-background border border-border">
          <span className="text-slate-500 dark:text-slate-400 text-[10px] uppercase font-sans font-semibold">
            Linhas Totais
          </span>
          <p className="text-base font-bold text-slate-900 dark:text-white mt-0.5">
            {parquetInspection.num_rows.toLocaleString()}
          </p>
        </div>
        <div className="p-3 rounded-xl bg-surface dark:bg-background border border-border">
          <span className="text-slate-500 dark:text-slate-400 text-[10px] uppercase font-sans font-semibold">
            Tamanho do Arquivo
          </span>
          <p className="text-base font-bold text-accent-cyan mt-0.5">
            {parquetInspection.size_mb} MB
          </p>
        </div>
        <div className="p-3 rounded-xl bg-surface dark:bg-background border border-border">
          <span className="text-slate-500 dark:text-slate-400 text-[10px] uppercase font-sans font-semibold">
            Colunas Detectadas
          </span>
          <p className="text-base font-bold text-emerald-600 dark:text-emerald-400 mt-0.5">
            {parquetInspection.columns.length}
          </p>
        </div>
      </div>

      <div className="space-y-1">
        <label className="text-slate-700 dark:text-slate-300 font-semibold font-sans">
          Colunas do Schema:
        </label>
        <div className="p-2 rounded-xl bg-surface dark:bg-background border border-border flex flex-wrap gap-1.5 max-h-24 overflow-y-auto">
          {parquetInspection.columns.map((c) => (
            <span
              key={c}
              className="px-2 py-0.5 rounded bg-surfaceHover dark:bg-surface border border-border text-[11px] font-mono text-slate-800 dark:text-slate-300"
            >
              {c}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};
