// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { Loader2, ShieldAlert, Activity, Lock, RefreshCw } from 'lucide-react';
import { OfficialReportData } from '../../../types/report';
import { Page1ExecutiveSummary } from './pages/Page1ExecutiveSummary';
import { Page2TechnicalAudit } from './pages/Page2TechnicalAudit';
import { Page3SafetyAndAttribution } from './pages/Page3SafetyAndAttribution';
import { Page4FormulasAndCounterfactual } from './pages/Page4FormulasAndCounterfactual';
import { Page5QuesitosAndLegal } from './pages/Page5QuesitosAndLegal';
import { Page6SignaturesAndReferences } from './pages/Page6SignaturesAndReferences';

interface XaiReportPreviewContainerProps {
  isLoadingReport: boolean;
  isDataReady?: boolean;
  generatingMessage?: string | null;
  reportError?: string | null;
  previewHtml: string | null;
  reportData: OfficialReportData | null;
  fontFamily: string;
  fontSize: number;
  lineSpacing: number;
  alignment: string;
  onRefresh?: () => void;
}

const TOTAL_PAGES = 6;

/**
 * Single Responsibility: Renders the ABNT A4 document preview sheets
 * applying dynamic CSS variables or fallback cards.
 * Enforces compliance lock screen when real telemetry data is not yet generated.
 */
export const XaiReportPreviewContainer: React.FC<XaiReportPreviewContainerProps> = ({
  isLoadingReport,
  isDataReady = true,
  generatingMessage,
  reportError,
  previewHtml,
  reportData,
  fontFamily,
  fontSize,
  lineSpacing,
  alignment,
  onRefresh,
}) => {
  const previewFontFamily =
    fontFamily === 'Arial' ? 'Arial, Helvetica, sans-serif' : '"Times New Roman", Times, serif';
  const previewLineHeight = lineSpacing === 1.5 ? '1.75' : lineSpacing === 1.15 ? '1.4' : '1.25';
  const previewTextAlign = alignment === 'left' ? 'left' : 'justify';

  if (isLoadingReport) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] p-12 space-y-4 text-center">
        <Loader2 className="w-10 h-10 text-emerald-500 animate-spin" />
        <div className="space-y-1">
          <h3 className="text-base font-bold text-slate-900 dark:text-white">
            Compilando Laudo Pericial de Tráfego no Backend...
          </h3>
          <p className="text-xs text-slate-600 dark:text-slate-400 max-w-md">
            O SYNAPSE está sintetizando telemetrias da malha, verificando guardrails do CONTRAN e formatando o parecer pericial conforme a norma ABNT NBR 10719.
          </p>
        </div>
      </div>
    );
  }

  if (reportError) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[440px] p-8 max-w-2xl mx-auto text-center">
        <div className="relative mb-6">
          <div className="w-20 h-20 rounded-2xl bg-rose-500/10 border border-rose-500/30 flex items-center justify-center text-rose-400 shadow-lg shadow-rose-500/10">
            <ShieldAlert className="w-10 h-10 animate-bounce" />
          </div>
        </div>

        <span className="px-3 py-1 text-xs font-mono font-bold tracking-wider uppercase bg-rose-500/20 text-rose-300 border border-rose-500/30 rounded-full mb-3">
          Falha de Comunicação / Backend
        </span>

        <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">
          Não foi possível compilar o Laudo Pericial
        </h3>

        <div className="w-full bg-slate-900/80 border border-rose-500/30 rounded-xl p-4 mb-6 text-left">
          <p className="text-xs text-rose-300 dark:text-rose-200 font-mono leading-relaxed">
            {reportError}
          </p>
        </div>

        {onRefresh && (
          <button
            onClick={onRefresh}
            className="px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold transition-all flex items-center gap-2 shadow-lg shadow-rose-950/30"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Tentar Novamente</span>
          </button>
        )}
      </div>
    );
  }

  if (!isDataReady || !reportData) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[440px] p-8 max-w-2xl mx-auto text-center">
        <div className="relative mb-6">
          <div className="w-20 h-20 rounded-2xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400 shadow-lg shadow-amber-500/10">
            <ShieldAlert className="w-10 h-10 animate-pulse" />
          </div>
          <div className="absolute -bottom-2 -right-2 bg-slate-900 border border-amber-500/40 rounded-full p-1.5 text-amber-400">
            <Activity className="w-4 h-4 animate-spin" />
          </div>
        </div>

        <span className="px-3 py-1 text-xs font-mono font-bold tracking-wider uppercase bg-amber-500/20 text-amber-300 border border-amber-500/30 rounded-full mb-3">
          Trava de Conformidade Operacional
        </span>

        <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">
          Dados de Telemetria em Processamento
        </h3>

        <p className="text-sm text-slate-600 dark:text-slate-300 mb-6 leading-relaxed">
          {generatingMessage ||
            'Os dados de telemetria e fusão neural estão sendo gerados na malha viária. Nenhum detector com telemetria ativa foi identificado no momento.'}
        </p>

        <div className="w-full bg-slate-900/60 dark:bg-slate-950/80 border border-slate-700/60 rounded-xl p-4 mb-6 text-left space-y-2">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
            <Lock className="w-3.5 h-3.5 text-amber-400" />
            <span>Diretriz de Integridade Pericial (Zero Dados Artificiais)</span>
          </div>
          <p className="text-xs text-slate-400 leading-relaxed font-sans">
            Em estrita observância ao CTB Art. 24 e Resoluções CONTRAN, o SYNAPSE não emite laudos periciais com estimativas sintéticas ou detectores fictícios. A geração oficial será desbloqueada assim que o pipeline neural MARKVART™ consolidar as leituras dos sensores ativos.
          </p>
        </div>

        {onRefresh && (
          <button
            onClick={onRefresh}
            className="px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold transition-all flex items-center gap-2 shadow-lg shadow-amber-950/30"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Verificar Telemetria Novamente</span>
          </button>
        )}
      </div>
    );
  }

  if (previewHtml) {
    return (
      <div
        id="official-traffic-audit-dossier"
        className="w-full flex flex-col items-center"
        style={{
          ['--report-font' as any]: previewFontFamily,
          ['--report-font-size' as any]: `${fontSize}pt`,
          ['--report-line-height' as any]: previewLineHeight,
          ['--report-align' as any]: previewTextAlign,
        }}
        dangerouslySetInnerHTML={{ __html: previewHtml }}
      />
    );
  }

  return (
    <div
      id="official-traffic-audit-dossier"
      className="space-y-6 transition-all duration-150"
      style={{
        fontFamily: previewFontFamily,
        textAlign: previewTextAlign as any,
        lineHeight: previewLineHeight,
        fontSize: `${fontSize}pt`,
      }}
    >
      <Page1ExecutiveSummary report={reportData} pageNumber={1} totalPages={TOTAL_PAGES} />
      <Page2TechnicalAudit report={reportData} pageNumber={2} totalPages={TOTAL_PAGES} />
      <Page3SafetyAndAttribution report={reportData} pageNumber={3} totalPages={TOTAL_PAGES} />
      <Page4FormulasAndCounterfactual report={reportData} pageNumber={4} totalPages={TOTAL_PAGES} />
      <Page5QuesitosAndLegal report={reportData} pageNumber={5} totalPages={TOTAL_PAGES} />
      <Page6SignaturesAndReferences report={reportData} pageNumber={6} totalPages={TOTAL_PAGES} />
    </div>
  );
};
