// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { CheckCircle2, Download } from 'lucide-react';
import { BatchImportResult } from '../../../types/sensors';

interface BatchSuccessViewProps {
  importResult: BatchImportResult;
  onDownloadConfig: () => void | Promise<void>;
}

export const BatchSuccessView: React.FC<BatchSuccessViewProps> = ({
  importResult,
  onDownloadConfig,
}) => {
  const localItems = importResult.items?.filter((item) => item.type === 'local') ?? [];
  const globalItems = importResult.items?.filter((item) => item.type === 'global') ?? [];

  return (
    <div className="py-6 text-center space-y-4">
      <div className="w-12 h-12 rounded-full bg-emerald-500/10 text-emerald-500 flex items-center justify-center mx-auto">
        <CheckCircle2 className="w-6 h-6" />
      </div>
      <div>
        <h3 className="text-sm font-bold text-slate-900 dark:text-white">
          {importResult.imported_count} Sensores Provisionados com Sucesso!
        </h3>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 max-w-md mx-auto">
          {localItems.length > 0 && globalItems.length > 0 ? (
            <>
              {localItems.length} sensores locais provisionados com URLs de envio e {globalItems.length} sensores globais conectados.
            </>
          ) : localItems.length > 0 ? (
            <>
              Todos os {localItems.length} sensores locais foram cadastrados no SYNAPSE com status{' '}
              <strong className="text-amber-500">Quarantine</strong> e vinculados à malha viária.
            </>
          ) : (
            <>
              Todos os {globalItems.length} sensores globais foram cadastrados e conectados aos seus feeds de dados.
            </>
          )}
        </p>
      </div>

      {localItems.length > 0 ? (
        <div className="pt-2 space-y-1.5">
          <button
            type="button"
            onClick={onDownloadConfig}
            className="inline-flex items-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold shadow-lg shadow-emerald-600/20 transition-all cursor-pointer"
          >
            <Download className="w-4 h-4" />
            <span>Baixar Planilha de Câmeras Locais (name, address)</span>
          </button>
          <p className="text-[11px] text-slate-400 dark:text-slate-500">
            Exporta as {localItems.length} câmeras com as URLs de envio geradas pelo SYNAPSE.
          </p>
        </div>
      ) : (
        <div className="pt-2 text-[11px] text-slate-400 dark:text-slate-500">
          Sensores globais operam via conexão pull (não requerem URLs locais de envio).
        </div>
      )}
    </div>
  );
};
