// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { useTranslation } from 'react-i18next';
import { Compass } from 'lucide-react';

interface MapEmptyStateProps {
  mapLoaded: boolean;
}

export const MapEmptyState: React.FC<MapEmptyStateProps> = ({ mapLoaded }) => {
  const { t } = useTranslation();

  if (mapLoaded) return null;

  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center bg-background/80 backdrop-blur-sm pointer-events-none select-none">
      <div className="w-16 h-16 rounded-2xl bg-primary-500/10 border border-primary-500/20 flex items-center justify-center mb-4">
        <Compass className="w-8 h-8 text-primary-500 dark:text-primary-400 animate-spin-slow" />
      </div>
      <h2 className="text-base font-bold text-slate-900 dark:text-white mb-2">{t('map.title')}</h2>
      <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm">{t('map.noMapLoaded')}</p>
    </div>
  );
};
