// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { useTranslation } from 'react-i18next';
import { Brain, Sparkles, Loader2, FileCheck } from 'lucide-react';

interface XaiHeaderControlsProps {
  isExplaining: boolean;
  onExplainDecision: () => void;
  onOpenReport: () => void;
}

export const XaiHeaderControls: React.FC<XaiHeaderControlsProps> = ({
  isExplaining,
  onExplainDecision,
  onOpenReport,
}) => {
  const { t } = useTranslation();

  return (
    <div className="glass-panel p-6 rounded-2xl flex items-center justify-between">
      <div>
        <h2 className="text-base font-bold text-slate-900 dark:text-white tracking-tight flex items-center gap-2">
          <Brain className="w-5 h-5 text-primary-500 dark:text-primary-400" />
          {t('xai.title')}
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          Interpretabilidade e auditoria de consistência física dos modelos neurais (iTransformer + GATv2).
        </p>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-3">
        {/* Action 1: Explicar Decisão Atual */}
        <button
          onClick={onExplainDecision}
          disabled={isExplaining}
          className="px-4 py-2 rounded-xl bg-surface border border-border text-xs font-semibold text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:border-primary-500/50 transition-all flex items-center gap-2 disabled:opacity-60 shadow-xs active:scale-95"
          title="Executar análise explicativa dos gradientes integrados da inferência atual"
        >
          {isExplaining ? (
            <Loader2 className="w-3.5 h-3.5 text-primary-500 animate-spin" />
          ) : (
            <Sparkles className="w-3.5 h-3.5 text-primary-500 dark:text-primary-400" />
          )}
          <span>{isExplaining ? t('xai.explaining') : t('xai.explainDecision')}</span>
        </button>

        {/* Action 2: Official Municipal Report (Laudo da Prefeitura) */}
        <button
          onClick={onOpenReport}
          className="px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-bold transition-all flex items-center gap-2 shadow-md shadow-emerald-600/20 border border-emerald-400/30 active:scale-95"
          title="Abrir laudo pericial oficial para prefeitura e órgãos reguladores"
        >
          <FileCheck className="w-4 h-4" />
          <span>{t('xai.generateReport')}</span>
        </button>
      </div>
    </div>
  );
};
