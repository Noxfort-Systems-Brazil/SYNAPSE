// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { FolderDown, X } from 'lucide-react';
import { SaveReportHeaderProps } from './types';

/**
 * Presentational Component: SaveReportHeader (SRP)
 * Renders the modal title, compliance badge, and dismissal control.
 */
export const SaveReportHeader: React.FC<SaveReportHeaderProps> = ({
  protocol,
  onClose,
  isDisabled,
}) => {
  return (
    <div className="flex items-center justify-between px-5 py-4 bg-slate-950/80 border-b border-slate-800">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-lg bg-blue-500/20 text-blue-400 border border-blue-500/30">
          <FolderDown className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-white tracking-wide">
            Salvar Laudo Técnico Oficial
          </h3>
          <p className="text-[11px] text-slate-400 font-mono">
            {protocol
              ? `Protocolo: ${protocol}`
              : 'Formato Microsoft Word (.docx) • Padrão ABNT NBR 10719'}
          </p>
        </div>
      </div>
      <button
        onClick={onClose}
        disabled={isDisabled}
        className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors disabled:opacity-40"
        title="Fechar modal"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
};
