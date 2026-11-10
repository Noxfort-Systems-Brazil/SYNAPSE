// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React, { useMemo } from 'react';
import { useTranslation } from 'react-i18next';
import { ShieldCheck, AlertTriangle, FileText, MapPin, Activity } from 'lucide-react';
import { XaiAuditVerdict, XaiResultItem } from '../../types/xai';
import { aggregateTopSensorAttributions } from '../../utils/chartOptions';

interface XaiSemanticPanelProps {
  result: XaiResultItem;
  latestVerdict?: XaiAuditVerdict;
}

export const XaiSemanticPanel: React.FC<XaiSemanticPanelProps> = ({ result, latestVerdict }) => {
  const { t } = useTranslation();

  const isSafe = latestVerdict ? latestVerdict.safe : true;

  // Extract top 3 most influential sensors
  const topSensors = useMemo(() => {
    return aggregateTopSensorAttributions(result.attributions, result.feature_names, 3);
  }, [result.attributions, result.feature_names]);

  // Clean human-friendly summary text
  const cleanSummary = useMemo(() => {
    if (result.id === 'initial') {
      return result.semantic_text;
    }
    const raw = result.semantic_text;
    if (raw && !raw.includes('(peso:')) {
      return raw;
    }
    return isSafe
      ? 'A inferência neural correlacionou a telemetria da malha viária e operou em regime estável. A decisão do plano de tráfego foi determinada predominantemente pela concentração de fluxo nos pontos destacados abaixo.'
      : 'Inconsistência física detectada pelo modelo Zero-Trust. A decisão foi submetida a veto preventivo de segurança para garantir a fluidez da malha viária.';
  }, [result.id, result.semantic_text, isSafe]);

  return (
    <div className="glass-panel p-6 rounded-2xl space-y-4">
      {/* Header with Title and Veredito Badge */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border/60 pb-3">
        <div className="flex items-center gap-2">
          <FileText className="w-4 h-4 text-accent-cyan" />
          <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
            {t('xai.executiveSummary')}
          </h3>
        </div>

        <div className="flex items-center gap-3 text-xs">
          {/* Status Badge */}
          <span
            className={`px-3 py-1 rounded-full text-[11px] font-bold flex items-center gap-1.5 ${
              isSafe
                ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30'
                : 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/30'
            }`}
          >
            {isSafe ? (
              <ShieldCheck className="w-3.5 h-3.5" />
            ) : (
              <AlertTriangle className="w-3.5 h-3.5" />
            )}
            <span>
              {isSafe
                ? t('xai.safeVerdict')
                : t('xai.vetoVerdict')}
            </span>
          </span>

          <span className="text-slate-400 dark:text-slate-500 font-mono text-[11px]">
            Δ: {result.convergence_delta.toFixed(4)}
          </span>

          {result.timestamp && (
            <span className="text-slate-400 dark:text-slate-500 font-mono text-[11px]">
              {result.timestamp}
            </span>
          )}
        </div>
      </div>

      {/* Textual Synthesis */}
      <div className="p-4 rounded-xl bg-surface dark:bg-background/80 border border-border text-xs text-slate-800 dark:text-slate-200 leading-relaxed font-sans shadow-xs">
        {cleanSummary}
      </div>

      {/* Top Influential Sensor Chips */}
      {topSensors.length > 0 && (
        <div className="pt-1">
          <div className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 mb-2 flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-primary-500" />
            <span>Sensores com Maior Peso na Decisão:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {topSensors.map((sensor, idx) => (
              <div
                key={sensor.name}
                className="px-3 py-1.5 rounded-xl bg-surface border border-border/80 text-xs flex items-center gap-2 shadow-xs hover:border-primary-500/40 transition-colors"
              >
                <MapPin className="w-3.5 h-3.5 text-primary-500 dark:text-primary-400" />
                <span className="font-semibold text-slate-900 dark:text-white">
                  {sensor.name}
                </span>
                <span className="px-1.5 py-0.5 rounded-md bg-primary-500/10 text-primary-600 dark:text-primary-400 font-mono text-[10px] font-bold">
                  {sensor.percentage}% de impacto
                </span>
                {idx === 0 && (
                  <span className="px-1.5 py-0.5 rounded-md bg-amber-500/10 text-amber-600 dark:text-amber-400 text-[10px] font-bold">
                    Principal
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
