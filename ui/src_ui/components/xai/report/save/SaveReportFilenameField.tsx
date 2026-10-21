// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { FileText, RotateCcw } from 'lucide-react';
import { SaveReportFilenameFieldProps } from './types';

/**
 * Presentational Component: SaveReportFilenameField (SRP)
 * Encapsulates the filename input with standard extension badge and reset capability.
 */
export const SaveReportFilenameField: React.FC<SaveReportFilenameFieldProps> = ({
  filename,
  defaultFilename,
  onFilenameChange,
  onResetFilename,
  isDisabled,
}) => {
  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <label className="text-xs font-semibold text-slate-200 flex items-center gap-1.5">
          <FileText className="w-3.5 h-3.5 text-blue-400" />
          <span>Qual nome deseja salvar:</span>
        </label>
        {filename !== defaultFilename && (
          <button
            type="button"
            onClick={onResetFilename}
            disabled={isDisabled}
            className="text-[11px] text-blue-400 hover:text-blue-300 flex items-center gap-1 transition-colors disabled:opacity-40"
            title="Restaurar nome oficial baseado no protocolo"
          >
            <RotateCcw className="w-3 h-3" />
            <span>Restaurar padrão</span>
          </button>
        )}
      </div>

      <div className="relative">
        <input
          type="text"
          value={filename}
          disabled={isDisabled}
          onChange={(e) => onFilenameChange(e.target.value)}
          placeholder="Ex: Laudo_Tecnico_Trafego_EXP-2026.docx"
          className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-700 rounded-lg text-xs font-mono text-white focus:outline-hidden focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors pr-16 disabled:opacity-50"
        />
        <span className="absolute right-3 top-2.5 text-xs font-mono text-slate-400 pointer-events-none">
          .docx
        </span>
      </div>
      <p className="text-[11px] text-slate-400 mt-1">
        O laudo é formatado em conformidade estrita com as normas ABNT NBR 10719 e NBR 14724.
      </p>
    </div>
  );
};
