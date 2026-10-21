// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { HardDrive, FolderOpen, Loader2 } from 'lucide-react';
import { SaveReportLocationPickerProps } from './types';

/**
 * Presentational Component: SaveReportLocationPicker (SRP)
 * Encapsulates destination selection between default Downloads and custom directory.
 */
export const SaveReportLocationPicker: React.FC<SaveReportLocationPickerProps> = ({
  saveLocationType,
  onLocationTypeChange,
  customDirectory,
  isPickingDir,
  onPickDirectory,
  isDisabled,
}) => {
  return (
    <div>
      <label className="text-xs font-semibold text-slate-200 flex items-center gap-1.5 mb-2">
        <HardDrive className="w-3.5 h-3.5 text-blue-400" />
        <span>Onde deseja salvar:</span>
      </label>

      <div className="space-y-2.5">
        {/* Opção Downloads (Padrão / Normal) */}
        <label
          className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
            saveLocationType === 'downloads'
              ? 'bg-blue-950/30 border-blue-500/50 text-white shadow-xs'
              : 'bg-slate-950/40 border-slate-800 text-slate-300 hover:border-slate-700'
          }`}
        >
          <input
            type="radio"
            name="saveLocation"
            checked={saveLocationType === 'downloads'}
            disabled={isDisabled}
            onChange={() => onLocationTypeChange('downloads')}
            className="mt-0.5 text-blue-600 focus:ring-blue-500"
          />
          <div className="flex-1">
            <div className="text-xs font-semibold flex items-center gap-1.5">
              <span>Pasta Downloads do Sistema (Padrão)</span>
              <span className="px-1.5 py-0.2 text-[9px] bg-slate-800 text-slate-400 rounded-sm font-mono">
                Normal
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-mono mt-0.5">
              Salva diretamente na pasta ~/Downloads do usuário
            </p>
          </div>
        </label>

        {/* Opção Pasta Personalizada */}
        <label
          className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all ${
            saveLocationType === 'custom'
              ? 'bg-blue-950/30 border-blue-500/50 text-white shadow-xs'
              : 'bg-slate-950/40 border-slate-800 text-slate-300 hover:border-slate-700'
          }`}
        >
          <input
            type="radio"
            name="saveLocation"
            checked={saveLocationType === 'custom'}
            disabled={isDisabled}
            onChange={() => onLocationTypeChange('custom')}
            className="mt-0.5 text-blue-600 focus:ring-blue-500"
          />
          <div className="flex-1">
            <div className="text-xs font-semibold flex items-center justify-between">
              <span>Escolher outra pasta no computador</span>
            </div>

            {saveLocationType === 'custom' && (
              <div className="mt-2.5 flex items-center gap-2">
                <div
                  className="flex-1 px-2.5 py-1.5 bg-slate-950 border border-slate-800 rounded-md text-[11px] font-mono text-slate-300 truncate"
                  title={customDirectory || undefined}
                >
                  {customDirectory || 'Nenhuma pasta selecionada'}
                </div>
                <button
                  type="button"
                  onClick={onPickDirectory}
                  disabled={isDisabled || isPickingDir}
                  className="px-2.5 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 flex items-center gap-1.5 transition-colors shrink-0 disabled:opacity-50"
                  title="Selecionar pasta de destino"
                >
                  {isPickingDir ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <FolderOpen className="w-3.5 h-3.5 text-amber-400" />
                  )}
                  <span>Procurar...</span>
                </button>
              </div>
            )}
          </div>
        </label>
      </div>
    </div>
  );
};
