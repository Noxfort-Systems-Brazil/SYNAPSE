// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React, { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import ReactECharts from 'echarts-for-react';
import { BarChart3 } from 'lucide-react';
import { createAttributionChartOption } from '../../utils/chartOptions';
import { useSystemStore } from '../../stores';

interface XaiAttributionChartProps {
  attributions: number[];
  featureNames?: string[];
}

export const XaiAttributionChart: React.FC<XaiAttributionChartProps> = ({
  attributions,
  featureNames,
}) => {
  const { t } = useTranslation();
  const theme = useSystemStore((s) => s.theme);
  const isDark = theme === 'dark';

  const otherLabel = t('xai.otherSensors');

  const attributionOption = useMemo(
    () => createAttributionChartOption(attributions, isDark, featureNames, otherLabel),
    [attributions, isDark, featureNames, otherLabel]
  );

  return (
    <div className="glass-panel p-6 rounded-2xl space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 border-b border-border/60 pb-3">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-primary-500 dark:text-primary-400" />
          <h3 className="text-xs font-bold text-slate-800 dark:text-white uppercase tracking-wider">
            {t('xai.sensorInfluence')}
          </h3>
        </div>
        <span className="text-[11px] text-slate-500 dark:text-slate-400 font-sans">
          {t('xai.topSensorsSubtitle')}
        </span>
      </div>
      <div className="h-72 w-full">
        <ReactECharts option={attributionOption} style={{ height: '100%', width: '100%' }} />
      </div>
    </div>
  );
};

