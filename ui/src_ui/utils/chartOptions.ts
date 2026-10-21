// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { TelemetryPoint } from '../types/sensors';
import { getThemeTokens } from '../theme';

export function createMseLossChartOption(points: TelemetryPoint[], isDark: boolean = true) {
  const tokens = getThemeTokens(isDark ? 'dark' : 'light');
  const { charts } = tokens.colors;
  const hasData = points && points.length > 0;
  const xData = hasData ? points.map((p) => p.time) : ['t-5', 't-4', 't-3', 't-2', 't-1', 't0'];
  const yData = hasData ? points.map((p) => p.value) : [];

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: charts.tooltipBg,
      borderColor: charts.tooltipBorder,
      textStyle: { color: charts.tooltipText, fontSize: 11 },
      extraCssText: isDark ? 'box-shadow: 0 4px 12px rgba(0,0,0,0.5);' : 'box-shadow: 0 4px 12px rgba(0,0,0,0.1);',
    },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '15%', containLabel: true },
    xAxis: {
      type: 'category',
      data: xData,
      axisLine: { lineStyle: { color: charts.axisLine } },
      axisLabel: { color: charts.axisLabel, fontSize: 10 },
    },
    yAxis: {
      type: 'value',
      name: 'MSE Loss',
      min: 0,
      max: hasData ? undefined : 0.05,
      nameTextStyle: { color: charts.axisLabel, fontSize: 10 },
      splitLine: { lineStyle: { color: charts.splitLine, type: 'dashed' } },
      axisLabel: { color: charts.yAxisLabel, fontSize: 10 },
    },
    series: [
      {
        name: 'MSE Loss',
        type: 'line',
        smooth: true,
        data: yData,
        showSymbol: true,
        symbolSize: 6,
        lineStyle: { color: '#f43f5e', width: 2.5 },
        itemStyle: { color: '#f43f5e' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(244, 63, 94, 0.25)' },
              { offset: 1, color: 'rgba(244, 63, 94, 0.0)' },
            ],
          },
        },
      },
    ],
  };
}

export function createDriftPsiChartOption(points: TelemetryPoint[], isDark: boolean = true) {
  const tokens = getThemeTokens(isDark ? 'dark' : 'light');
  const { charts } = tokens.colors;
  const hasData = points && points.length > 0;
  const xData = hasData ? points.map((p) => p.time) : ['t-5', 't-4', 't-3', 't-2', 't-1', 't0'];
  const yData = hasData ? points.map((p) => p.value) : [];

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: charts.tooltipBg,
      borderColor: charts.tooltipBorder,
      textStyle: { color: charts.tooltipText, fontSize: 11 },
      extraCssText: isDark ? 'box-shadow: 0 4px 12px rgba(0,0,0,0.5);' : 'box-shadow: 0 4px 12px rgba(0,0,0,0.1);',
    },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '15%', containLabel: true },
    xAxis: {
      type: 'category',
      data: xData,
      axisLine: { lineStyle: { color: charts.axisLine } },
      axisLabel: { color: charts.axisLabel, fontSize: 10 },
    },
    yAxis: {
      type: 'value',
      name: 'PSI Score',
      min: 0,
      max: hasData ? undefined : 0.10,
      nameTextStyle: { color: charts.axisLabel, fontSize: 10 },
      splitLine: { lineStyle: { color: charts.splitLine, type: 'dashed' } },
      axisLabel: { color: charts.yAxisLabel, fontSize: 10 },
    },
    series: [
      {
        name: 'PSI Value',
        type: 'line',
        smooth: true,
        data: yData,
        showSymbol: true,
        symbolSize: 6,
        lineStyle: { color: '#3b82f6', width: 2.5 },
        itemStyle: { color: '#3b82f6' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(59, 130, 246, 0.25)' },
              { offset: 1, color: 'rgba(59, 130, 246, 0.0)' },
            ],
          },
        },
      },
    ],
  };
}

// Domain attribution aggregator imported from specialized service (Clean Architecture / SRP)
import {
  aggregateTopSensorAttributions,
  type AggregatedFeatureItem,
} from '../services/xai';

export { aggregateTopSensorAttributions, type AggregatedFeatureItem };

export function createAttributionChartOption(
  attributions: number[],
  isDark: boolean = true,
  featureNames?: string[],
  otherLabel?: string
) {
  const tokens = getThemeTokens(isDark ? 'dark' : 'light');
  const { charts } = tokens.colors;

  const aggregated = aggregateTopSensorAttributions(
    attributions,
    featureNames,
    6,
    otherLabel || 'Demais Sensores (Agregados)'
  );

  // ECharts horizontal bar charts: reverse so the highest rank is at the top
  const reversed = [...aggregated].reverse();
  const yData = reversed.map((item) => item.name);
  const xData = reversed.map((item) => item.percentage);
  const weights = reversed.map((item) => item.weight);

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: charts.tooltipBg,
      borderColor: charts.tooltipBorder,
      textStyle: { color: charts.tooltipText, fontSize: 12 },
      extraCssText: isDark ? 'box-shadow: 0 4px 12px rgba(0,0,0,0.5);' : 'box-shadow: 0 4px 12px rgba(0,0,0,0.1);',
      formatter: (params: any) => {
        const item = Array.isArray(params) ? params[0] : params;
        if (!item) return '';
        const idx = item.dataIndex;
        const weightVal = weights[idx] ?? 0;
        return `
          <div style="font-family: inherit; font-size: 12px; line-height: 1.5;">
            <div style="font-weight: bold; margin-bottom: 2px;">${item.name}</div>
            <div style="color: #38bdf8;">Contribuição Relativa: <b>${item.value}%</b></div>
            <div style="color: #94a3b8; font-size: 11px;">Peso Acumulado: ${weightVal}</div>
          </div>
        `;
      },
    },
    grid: { left: '3%', right: '8%', bottom: '4%', top: '6%', containLabel: true },
    xAxis: {
      type: 'value',
      name: 'Influência Relativa (%)',
      nameTextStyle: { color: charts.axisLabel, fontSize: 10, padding: [0, 0, 0, 10] },
      axisLine: { lineStyle: { color: charts.axisLine } },
      splitLine: { lineStyle: { color: charts.splitLine, type: 'dashed' } },
      axisLabel: {
        color: charts.axisLabel,
        fontSize: 10,
        formatter: '{value}%',
      },
      max: (value: { max: number }) => Math.min(100, Math.ceil((value.max + 5) / 10) * 10),
    },
    yAxis: {
      type: 'category',
      data: yData,
      axisLine: { lineStyle: { color: charts.axisLine } },
      axisTick: { show: false },
      axisLabel: {
        color: charts.axisLabel,
        fontSize: 11,
        fontWeight: 'bold',
        formatter: (val: string) => (val.length > 25 ? `${val.substring(0, 23)}...` : val),
      },
    },
    series: [
      {
        name: 'Influência na Decisão',
        type: 'bar',
        barWidth: 20,
        data: xData,
        label: {
          show: true,
          position: 'right',
          formatter: '{c}%',
          color: isDark ? '#e2e8f0' : '#1e293b',
          fontWeight: 'bold',
          fontSize: 11,
        },
        itemStyle: {
          color: (params: any) => {
            const isTop = params.dataIndex === reversed.length - 1;
            return {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 1,
              y2: 0,
              colorStops: isTop
                ? [
                    { offset: 0, color: '#38bdf8' },
                    { offset: 1, color: '#0ea5e9' },
                  ]
                : [
                    { offset: 0, color: '#3b82f6' },
                    { offset: 1, color: '#6366f1' },
                  ],
            };
          },
          borderRadius: [0, 6, 6, 0],
        },
      },
    ],
  };
}


