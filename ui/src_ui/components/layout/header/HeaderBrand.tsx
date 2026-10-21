// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { useTranslation } from 'react-i18next';

/**
 * Atomic subcomponent for brand and visual identity display (SRP).
 */
export const HeaderBrand: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="flex items-center gap-2.5 sm:gap-3 shrink-0 min-w-0">
      <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-br from-primary-500/20 via-amber-500/10 to-transparent p-1 shadow-md shadow-primary-500/10 flex items-center justify-center border border-primary-500/20 bg-background/50 shrink-0">
        <img src="/logo.png" alt="SYNAPSE Logo" className="w-full h-full object-contain drop-shadow" />
      </div>
      <div className="min-w-0">
        <div className="flex items-center gap-1.5 sm:gap-2">
          <h1 className="font-bold text-base sm:text-lg tracking-tight bg-gradient-to-r from-slate-900 via-slate-700 to-slate-500 dark:from-white dark:via-slate-200 dark:to-slate-400 bg-clip-text text-transparent whitespace-nowrap">
            {t('app.title')}
          </h1>
          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-primary-500/15 text-primary-600 dark:text-primary-300 border border-primary-500/25 shrink-0 whitespace-nowrap">
            v2.0
          </span>
        </div>
        <p className="hidden xl:block text-xs text-slate-500 dark:text-slate-400 font-medium truncate max-w-[260px] 2xl:max-w-none whitespace-nowrap">
          {t('app.subtitle')}
        </p>
      </div>
    </div>
  );
};
