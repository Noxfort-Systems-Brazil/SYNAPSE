// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React, { useState, useMemo } from 'react';
import {
  X,
  FileCheck,
  Printer,
  ShieldCheck,
  ShieldAlert,
  FileText,
  Loader2,
  SlidersHorizontal,
  CheckCircle2,
} from 'lucide-react';
import { XaiResultItem } from '../../types/xai';
import { IReportBuilder, OfficialReportData } from '../../types/report';
import { useReportStore } from '../../stores';
import { useReportTypographyStore } from '../../stores/useReportTypographyStore';
import { systemService } from '../../services/api/SystemService';
import { ReportTypographyToolbar } from './report/ReportTypographyToolbar';
import { XaiReportPreviewContainer } from './report/XaiReportPreviewContainer';


interface XaiOfficialReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  result?: XaiResultItem | null;
  reportBuilder?: IReportBuilder;
}

/**
 * Official Traffic Engineering & Municipal Operations Audit Report Modal.
 * Standardized in strict compliance with ABNT NBR 10719, NBR 14724, CTB Art. 24, and CONTRAN.
 * Enforces Operational Compliance Lock Guard: reports are compiled strictly from active telemetry.
 */
export const XaiOfficialReportModal: React.FC<XaiOfficialReportModalProps> = ({
  isOpen,
  onClose,
  result,
}) => {
  const [exportingDocxLocal, setExportingDocxLocal] = useState(false);
  const [showFormatControls, setShowFormatControls] = useState(false);
  const [savedPathFeedback, setSavedPathFeedback] = useState<string | null>(null);

  const {
    isLoadingReport,
    selectedReport,
    previewHtml,
    exportDocx,
    isExportingDocx,
    isDataReady,
    generatingMessage,
    reportError,
    fetchOfficialReport,
  } = useReportStore();

  // Typography Preferences from Store
  const { fontFamily, fontSize, lineSpacing, alignment } = useReportTypographyStore();

  // Strict Real Data: consumes backend live report. Zero fake fallbacks.
  const reportData = selectedReport;

  const defaultFilename = useMemo(() => {
    const proto = reportData?.protocol || result?.id || 'RELATORIO';
    const cleanProto = proto.replace(/[^a-zA-Z0-9_-]/g, '_');
    return `Laudo_Tecnico_Trafego_${cleanProto}.docx`;
  }, [reportData?.protocol, result?.id]);

  if (!isOpen) return null;

  const handleExportDocx = async (outputPath?: string) => {
    setExportingDocxLocal(true);
    setSavedPathFeedback(null);
    try {
      const res = await exportDocx(outputPath);
      if (res.success) {
        console.log(`Laudo Oficial exportado com sucesso para DOCX: ${res.output_path}`);
        if (res.output_path) {
          setSavedPathFeedback(res.output_path);
        }
      } else {
        console.error('Erro ao exportar DOCX via backend:', res.error);
      }
    } catch (e) {
      console.error('Error generating DOCX:', e);
    } finally {
      setExportingDocxLocal(false);
    }
  };

  const handleSaveDocx = async () => {
    try {
      const res = await systemService.saveFile({
        defaultFilename,
        title: 'Salvar Laudo Técnico Oficial (.docx)',
        filterName: 'Documento Word (*.docx)',
        extensions: ['docx'],
      });

      if (res.path && !res.cancelled) {
        await handleExportDocx(res.path);
      }
    } catch (err) {
      console.error('Erro ao acionar diálogo de salvamento do laudo:', err);
    }
  };

  const handlePrint = () => {
    window.print();
  };


  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-md p-2 sm:p-4 overflow-y-auto animate-in fade-in duration-200">
      <div className="relative w-full max-w-[230mm] max-h-[96vh] flex flex-col bg-slate-200 dark:bg-slate-900 border border-slate-400 dark:border-slate-700 shadow-2xl rounded-2xl overflow-hidden">
        
        {/* Barra de Ferramentas Superior */}
        <div className="flex items-center justify-between px-5 py-3.5 bg-slate-900 text-white border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
              <FileCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold tracking-wide">
                  Laudo Técnico & Relatório de Auditoria de Tráfego
                </h2>
                {isDataReady && reportData ? (
                  <span className="px-2 py-0.5 text-[10px] font-mono font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30 rounded-xs">
                    Word (.docx) / ABNT
                  </span>
                ) : (
                  <span className="px-2 py-0.5 text-[10px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/30 rounded-xs">
                    TRAVA ATIVA (GERANDO DADOS)
                  </span>
                )}
              </div>
              <p className="text-[11px] text-slate-300 font-mono">
                {reportData
                  ? `Protocolo: ${reportData.protocol} • Processo: ${reportData.processNumber}`
                  : 'Aguardando telemetria ativa da malha viária...'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Botão para alternar a Barra de Tipografia */}
            <button
              onClick={() => setShowFormatControls(!showFormatControls)}
              disabled={!isDataReady || !reportData}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 border disabled:opacity-40 disabled:cursor-not-allowed ${
                showFormatControls
                  ? 'bg-blue-600 border-blue-500 text-white shadow-sm'
                  : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700'
              }`}
              title="Ajustar tamanho da fonte, espaçamento e alinhamento do laudo"
            >
              <SlidersHorizontal className="w-3.5 h-3.5" />
              <span>Formatação</span>
              <span className="text-[10px] bg-slate-950/40 px-1.5 py-0.5 rounded-sm font-mono text-slate-300">
                {fontFamily} • {fontSize}pt • {lineSpacing}x
              </span>
            </button>

            {/* Imprimir */}
            <button
              onClick={handlePrint}
              disabled={!isDataReady || !reportData}
              className="p-1.5 rounded-lg bg-slate-800 border border-slate-700 hover:bg-slate-700 text-slate-300 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
              title={!isDataReady ? "Dados em processamento" : "Imprimir visualização do laudo"}
            >
              <Printer className="w-4 h-4" />
            </button>

            {/* Salvar DOCX (Diálogo nativo para escolher onde salvar) */}
            <button
              onClick={handleSaveDocx}
              disabled={!isDataReady || !reportData || isExportingDocx || exportingDocxLocal}
              className="px-3.5 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 active:scale-95 text-white text-xs font-bold transition-all flex items-center gap-1.5 shadow-lg shadow-blue-950/40 disabled:opacity-40 disabled:cursor-not-allowed"
              title={!isDataReady ? "Trava Operacional Ativa: exportação bloqueada enquanto dados são gerados" : "Escolher local e salvar laudo pericial (.docx)"}
            >
              {isExportingDocx || exportingDocxLocal ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Salvando...</span>
                </>
              ) : (
                <>
                  <FileText className="w-4 h-4" />
                  <span>Salvar DOCX</span>
                </>
              )}
            </button>

            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors ml-1"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Subcomponente Especializado: Barra de Tipografia (SRP) */}
        <ReportTypographyToolbar isVisible={showFormatControls} />

        {/* Banner de Sucesso de Salvamento */}
        {savedPathFeedback && (
          <div className="mx-5 my-2 p-3 bg-emerald-950/80 border border-emerald-500/40 rounded-xl flex items-center justify-between text-xs text-emerald-200 animate-in fade-in duration-200 shadow-lg">
            <div className="flex items-center gap-2.5 overflow-hidden">
              <div className="p-1.5 rounded-full bg-emerald-500/20 text-emerald-400 shrink-0">
                <CheckCircle2 className="w-4 h-4" />
              </div>
              <div className="truncate">
                <div className="font-bold text-white flex items-center gap-2">
                  <span>Laudo Oficial DOCX exportado com sucesso!</span>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 bg-emerald-500/20 text-emerald-300 rounded-sm">ABNT NBR 10719</span>
                </div>
                <div className="text-[11px] text-emerald-300 font-mono truncate mt-0.5" title={savedPathFeedback}>
                  Salvo em: <span className="underline font-semibold">{savedPathFeedback}</span>
                </div>
              </div>
            </div>
            <button
              onClick={() => setSavedPathFeedback(null)}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-emerald-900/40 transition-colors ml-3 shrink-0"
              title="Fechar notificação"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Banner de Conformidade e Resumo de Configuração */}
        <div className="px-5 py-2 bg-slate-950/90 text-[11px] text-slate-300 flex items-center justify-between border-b border-slate-800 font-mono">
          <div className="flex items-center gap-2">
            {isDataReady && reportData ? (
              <>
                <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />
                <span>Formato Nativo: Microsoft Word (.docx) • Padrão Editorial ABNT NBR 10719 & NBR 6023 • CTB Art. 24</span>
              </>
            ) : (
              <>
                <ShieldAlert className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
                <span className="text-amber-300">
                  Trava Operacional Ativa: Telemetria e fusão neural em processamento na malha viária
                </span>
              </>
            )}
          </div>
          <span className="text-slate-400">
            {isDataReady && reportData
              ? `Configuração Ativa: ${fontFamily} • ${fontSize}pt • ${lineSpacing}x • ${alignment === 'justify' ? 'Justificado' : 'À Esquerda'}`
              : 'MARKVART™ Gateway de Percepção'}
          </span>
        </div>

        {/* Conteúdo do Laudo com as Folhas ABNT e Estilos Tipográficos Dinâmicos */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 bg-slate-300 dark:bg-slate-950/70">
          <XaiReportPreviewContainer
            isLoadingReport={isLoadingReport}
            isDataReady={isDataReady}
            generatingMessage={generatingMessage}
            reportError={reportError}
            previewHtml={previewHtml}
            reportData={reportData}
            fontFamily={fontFamily}
            fontSize={fontSize}
            lineSpacing={lineSpacing}
            alignment={alignment}
            onRefresh={() => fetchOfficialReport(result?.id, result)}
          />
        </div>

      </div>
    </div>
  );
};

