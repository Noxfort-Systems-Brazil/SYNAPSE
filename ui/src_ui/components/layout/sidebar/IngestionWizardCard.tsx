// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { useTranslation } from 'react-i18next';
import { Sparkles, ArrowRight } from 'lucide-react';

interface IngestionWizardCardProps {
  openImportWizard: (step?: 1 | 2 | 3) => void;
  disabled?: boolean;
}

/**
 * Single Responsibility Principle (SRP):
 * Renders the quick-access card to initiate the sequential ingestion workflow (Map -> Parquet -> Sensors).
 */
export const IngestionWizardCard: React.FC<IngestionWizardCardProps> = ({
  openImportWizard,
  disabled = false,
}) => {
  const { t } = useTranslation();

  return (
    <div className="space-y-2">
      <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider px-1">
        {t('wizard.title')}
      </span>
      <button
        type="button"
        onClick={() => openImportWizard(1)}
        disabled={disabled}
        title="Iniciar fluxo sequencial de ingestão de dados"
        className={`w-full p-3 rounded-xl bg-surface border border-border hover:border-primary-500/50 text-slate-700 dark:text-slate-200 hover:text-slate-900 dark:hover:text-white transition-all flex items-center justify-between group shadow-sm hover:shadow-primary-500/10 ${
          disabled ? 'opacity-50 pointer-events-none cursor-not-allowed' : ''
        }`}
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-primary-500/10 border border-primary-500/20 flex items-center justify-center text-primary-500 dark:text-primary-400 group-hover:scale-105 transition-transform">
            <Sparkles className="w-4 h-4" />
          </div>
          <div className="text-left">
            <div className="text-xs font-bold text-slate-900 dark:text-white flex items-center gap-1.5">
              <span>Fluxo de Ingestão</span>
            </div>
            <div className="text-[10px] text-slate-500 dark:text-slate-400 font-medium flex items-center gap-1 mt-0.5">
              <span className="text-primary-600 dark:text-primary-300">Mapa</span>
              <span className="text-slate-400 dark:text-slate-500">→</span>
              <span className="text-accent-cyan">Parquet</span>
              <span className="text-slate-400 dark:text-slate-500">→</span>
              <span className="text-emerald-500 dark:text-emerald-400">Sensores</span>
            </div>
          </div>
        </div>
        <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-slate-900 dark:group-hover:text-white group-hover:translate-x-0.5 transition-all" />
      </button>
    </div>
  );
};
