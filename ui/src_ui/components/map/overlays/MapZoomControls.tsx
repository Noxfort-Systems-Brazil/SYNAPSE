// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { useTranslation } from 'react-i18next';
import { ZoomIn, ZoomOut, Maximize2 } from 'lucide-react';

interface MapZoomControlsProps {
  onZoomIn: () => void;
  onZoomOut: () => void;
  onResetView?: () => void;
}

export const MapZoomControls: React.FC<MapZoomControlsProps> = ({
  onZoomIn,
  onZoomOut,
  onResetView,
}) => {
  const { t } = useTranslation();

  return (
    <div className="absolute top-4 right-4 flex flex-col gap-2 z-10 select-none">
      <button
        onClick={onZoomIn}
        title={t('map.zoomIn')}
        className="p-2.5 rounded-xl glass-panel text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white glass-panel-hover transition-colors"
      >
        <ZoomIn className="w-4 h-4" />
      </button>
      <button
        onClick={onZoomOut}
        title={t('map.zoomOut')}
        className="p-2.5 rounded-xl glass-panel text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white glass-panel-hover transition-colors"
      >
        <ZoomOut className="w-4 h-4" />
      </button>
      {onResetView && (
        <button
          onClick={onResetView}
          title={t('map.resetView')}
          className="p-2.5 rounded-xl glass-panel text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white glass-panel-hover transition-colors"
        >
          <Maximize2 className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};
