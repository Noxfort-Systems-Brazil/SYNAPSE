// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { useTranslation } from 'react-i18next';
import { FolderOpen } from 'lucide-react';

interface ParquetSelectStepProps {
  filePath: string;
  setFilePath: (val: string) => void;
  isBrowsing: boolean;
  onBrowseFile: () => void;
  errorMessage: string | null;
}

export const ParquetSelectStep: React.FC<ParquetSelectStepProps> = ({
  filePath,
  setFilePath,
  isBrowsing,
  onBrowseFile,
  errorMessage,
}) => {
  const { t } = useTranslation();

  return (
    <div className="space-y-4 text-xs">
      <div className="p-3 bg-sky-50 dark:bg-primary-500/10 border border-sky-200 dark:border-primary-500/20 rounded-xl text-sky-900 dark:text-primary-300">
        Selecione a base histórica em formato Parquet (
        <code className="font-mono font-bold text-sky-950 dark:text-white">.parquet</code>) contendo
        séries temporais de tráfego.
      </div>

      <div className="space-y-1.5">
        <label className="text-slate-700 dark:text-slate-300 font-semibold">
          Caminho do Arquivo no Disco (.parquet):
        </label>
        <div className="flex items-center gap-2">
          <input
            type="text"
            placeholder="/caminho/para/dataset.parquet"
            value={filePath}
            onChange={(e) => setFilePath(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                onBrowseFile();
              }
            }}
            className="flex-1 h-10 px-3 bg-surface dark:bg-background border border-border rounded-xl text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-primary-500 font-mono text-xs"
          />
          <button
            type="button"
            onClick={onBrowseFile}
            disabled={isBrowsing}
            title={isBrowsing ? 'Abrindo seletor de arquivos...' : t('wizard.browseTooltip')}
            className={`h-10 px-3.5 bg-surface border border-border text-slate-700 dark:text-slate-300 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all shadow-sm group ${
              isBrowsing
                ? 'opacity-50 cursor-not-allowed'
                : 'hover:border-accent-cyan hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <FolderOpen
              className={`w-4 h-4 text-accent-cyan ${
                isBrowsing ? 'animate-pulse' : 'group-hover:scale-110'
              } transition-transform`}
            />
            <span>{isBrowsing ? 'Aguarde...' : t('wizard.browse')}</span>
          </button>
        </div>
      </div>

      {errorMessage && (
        <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/60 border border-rose-200 dark:border-rose-500/40 text-rose-700 dark:text-rose-300">
          {errorMessage}
        </div>
      )}
    </div>
  );
};
