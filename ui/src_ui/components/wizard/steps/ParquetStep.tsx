// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { useTranslation } from 'react-i18next';
import { Database, ArrowRight } from 'lucide-react';
import {
  useParquetImport,
  ParquetSelectStep,
  ParquetInspectStep,
  ParquetProgressStep,
} from '../parquet';

export const ParquetStep: React.FC = () => {
  const { t } = useTranslation();
  const etl = useParquetImport(true, () => {});

  return (
    <div className="space-y-4 animate-in fade-in">
      {/* Information Header */}
      <div className="p-3.5 bg-sky-50 dark:bg-accent-cyan/10 border border-sky-200 dark:border-accent-cyan/20 rounded-xl text-sky-800 dark:text-accent-cyan flex items-start gap-2.5">
        <Database className="w-4 h-4 text-sky-600 dark:text-accent-cyan flex-shrink-0 mt-0.5" />
        <div>
          <p className="font-bold text-slate-900 dark:text-white">{t('wizard.parquetTitle')}</p>
          <p className="text-[11px] text-slate-600 dark:text-slate-300 mt-0.5">{t('wizard.parquetDesc')}</p>
        </div>
      </div>

      {/* Hidden file input for web fallback */}
      <input
        ref={etl.fileInputRef}
        type="file"
        accept=".parquet"
        onChange={etl.handleFileInputChange}
        className="hidden"
      />

      {/* Sub-step 1: File selection & inspection trigger */}
      {etl.step === 1 && (
        <ParquetSelectStep
          filePath={etl.filePath}
          setFilePath={etl.setFilePath}
          isBrowsing={etl.isBrowsing}
          onBrowseFile={etl.handleBrowseFile}
          errorMessage={etl.errorMessage}
        />
      )}

      {/* Sub-step 2: Inspection results & confirmation */}
      {etl.step === 2 && etl.parquetInspection && (
        <div className="space-y-4">
          <ParquetInspectStep parquetInspection={etl.parquetInspection} />
          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={() => etl.setStep(1)}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors"
            >
              {t('common.cancel', 'Voltar')}
            </button>
            <button
              type="button"
              onClick={etl.handleExecuteImport}
              className="px-5 py-2 rounded-xl bg-primary-600 hover:bg-primary-500 text-white text-xs font-bold transition-all shadow-md flex items-center gap-2"
            >
              <span>{t('wizard.startImport', 'Iniciar Ingestão Parquet')}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}

      {/* Sub-step 3: Real-time progress bar */}
      {etl.step === 3 && (
        <ParquetProgressStep importProgress={etl.importProgress} />
      )}
    </div>
  );
};
