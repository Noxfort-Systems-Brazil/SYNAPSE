// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { Check, Loader2 } from 'lucide-react';
import { SaveReportActionButtonsProps } from './types';

/**
 * Presentational Component: SaveReportActionButtons (SRP)
 * Renders the modal footer actions: Cancel and Save Laudo DOCX.
 */
export const SaveReportActionButtons: React.FC<SaveReportActionButtonsProps> = ({
  isSaving,
  isDisabled,
  onCancel,
}) => {
  return (
    <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-slate-800">
      <button
        type="button"
        onClick={onCancel}
        disabled={isDisabled}
        className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-400 hover:text-white hover:bg-slate-800 transition-colors disabled:opacity-50"
      >
        Cancelar
      </button>

      <button
        type="submit"
        disabled={isDisabled}
        className="px-5 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 active:scale-95 text-white text-xs font-bold transition-all flex items-center gap-2 shadow-lg shadow-blue-950/50 disabled:opacity-50"
      >
        {isSaving ? (
          <>
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
            <span>Salvando Laudo...</span>
          </>
        ) : (
          <>
            <Check className="w-3.5 h-3.5" />
            <span>Salvar Laudo DOCX</span>
          </>
        )}
      </button>
    </div>
  );
};
