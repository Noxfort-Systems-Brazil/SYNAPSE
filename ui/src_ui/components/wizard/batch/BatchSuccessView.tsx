// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { CheckCircle2, Download } from 'lucide-react';
import { BatchImportResult } from '../../../types/sensors';

interface BatchSuccessViewProps {
  importResult: BatchImportResult;
  onDownloadConfig: () => void;
}

export const BatchSuccessView: React.FC<BatchSuccessViewProps> = ({
  importResult,
  onDownloadConfig,
}) => {
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
          Todos os sensores foram cadastrados no SYNAPSE com status{' '}
          <strong className="text-amber-500">Quarantine</strong> e vinculados aos seus nós/arestas.
          Cada um possui uma URL dedicada para envio de dados.
        </p>
      </div>

      <div className="pt-2">
        <button
          type="button"
          onClick={onDownloadConfig}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-semibold shadow-lg shadow-emerald-600/20 transition-all cursor-pointer"
        >
          <Download className="w-4 h-4" />
          <span>Baixar Tabela de Configuração das Câmeras (config_cameras.csv)</span>
        </button>
      </div>
    </div>
  );
};
