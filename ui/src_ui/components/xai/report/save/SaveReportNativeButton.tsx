// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { Monitor, Loader2 } from 'lucide-react';
import { SaveReportNativeButtonProps } from './types';

/**
 * Presentational Component: SaveReportNativeButton (SRP)
 * Provides a one-click trigger to invoke the platform native save file dialog.
 */
export const SaveReportNativeButton: React.FC<SaveReportNativeButtonProps> = ({
  isPickingNative,
  onNativeSaveDialog,
  isDisabled,
}) => {
  return (
    <div className="pt-2 border-t border-slate-800/80">
      <button
        type="button"
        onClick={onNativeSaveDialog}
        disabled={isDisabled || isPickingNative}
        className="w-full py-2 px-3 rounded-lg bg-slate-800/70 hover:bg-slate-800 border border-slate-700 text-slate-300 hover:text-white text-xs font-medium flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
        title="Abrir a janela nativa do sistema operacional (Zenity / GTK / Windows)"
      >
        {isPickingNative ? (
          <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-400" />
        ) : (
          <Monitor className="w-3.5 h-3.5 text-blue-400" />
        )}
        <span>Ou abrir diálogo nativo do sistema operacional (Zenity / Salvar Como...)</span>
      </button>
    </div>
  );
};
