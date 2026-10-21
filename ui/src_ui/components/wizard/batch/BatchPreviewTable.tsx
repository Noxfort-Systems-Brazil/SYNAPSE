// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { FileText, MapPin, AlertTriangle, Check } from 'lucide-react';
import { BatchPreviewResult, BatchPreviewItem } from '../../../types/sensors';

interface BatchPreviewTableProps {
  previewData: BatchPreviewResult;
}

const ResolvedTypeBadge: React.FC<{ type: BatchPreviewItem['resolved_type'] }> = ({ type }) => {
  switch (type) {
    case 'NODE':
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-semibold text-[10px]">
          <MapPin className="w-3 h-3" /> Nó / Cruzamento
        </span>
      );
    case 'EDGE':
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-sky-500/10 text-sky-600 dark:text-sky-400 font-semibold text-[10px]">
          Aresta / Rua
        </span>
      );
    case 'UNKNOWN':
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-amber-500/10 text-amber-600 dark:text-amber-400 font-semibold text-[10px]">
          Pendente
        </span>
      );
    case 'INVALID':
    default:
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-rose-500/10 text-rose-600 dark:text-rose-400 font-semibold text-[10px]">
          Não Encontrado
        </span>
      );
  }
};

export const BatchPreviewTable: React.FC<BatchPreviewTableProps> = ({ previewData }) => {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
          <FileText className="w-4 h-4 text-primary-500" />
          <span>Prévia da Validação Topológica (Dry-Run)</span>
        </h3>

        <div className="flex items-center gap-2 text-xs">
          <span className="px-2 py-0.5 rounded-full bg-slate-500/10 text-slate-600 dark:text-slate-400 font-mono text-[11px]">
            Total: {previewData.total}
          </span>
          <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-medium text-[11px]">
            Válidos: {previewData.valid_count}
          </span>
          {previewData.error_count > 0 && (
            <span className="px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-600 dark:text-rose-400 font-medium text-[11px]">
              Alertas: {previewData.error_count}
            </span>
          )}
        </div>
      </div>

      <div className="border border-border/80 rounded-xl overflow-hidden max-h-56 overflow-y-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-surfaceHover/80 sticky top-0 border-b border-border/80 text-slate-500 dark:text-slate-400">
            <tr>
              <th className="p-2.5 font-semibold w-12">Linha</th>
              <th className="p-2.5 font-semibold">Nome do Sensor</th>
              <th className="p-2.5 font-semibold">Localização Informada</th>
              <th className="p-2.5 font-semibold">Tipo Resolvido</th>
              <th className="p-2.5 font-semibold">Diagnóstico</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border/60">
            {previewData.items.map((item, idx) => (
              <tr
                key={idx}
                className={`hover:bg-surfaceHover/40 transition-colors ${
                  item.resolved_type === 'INVALID' ? 'bg-rose-500/5' : ''
                }`}
              >
                <td className="p-2.5 font-mono text-slate-400 text-[11px]">{item.line}</td>
                <td className="p-2.5 font-medium text-slate-800 dark:text-slate-200">
                  {item.name}
                </td>
                <td className="p-2.5 font-mono text-[11px] text-slate-600 dark:text-slate-400">
                  {item.location}
                </td>
                <td className="p-2.5">
                  <ResolvedTypeBadge type={item.resolved_type} />
                </td>
                <td className="p-2.5 text-[11px]">
                  {item.error ? (
                    <span className="text-rose-500 flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3 flex-shrink-0" />
                      {item.error}
                    </span>
                  ) : (
                    <span className="text-emerald-500 flex items-center gap-1">
                      <Check className="w-3 h-3 flex-shrink-0" />
                      Pronto para cadastro
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
