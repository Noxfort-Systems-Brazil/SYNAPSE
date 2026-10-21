// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { create } from 'zustand';
import { OfficialReportData } from '../types/report';
import { xaiService } from '../services/api/XaiService';
import { useMunicipalSettingsStore } from './useMunicipalSettingsStore';
import { useReportTypographyStore } from './useReportTypographyStore';
import { useSystemStore } from './useSystemStore';

interface ReportStoreState {
  selectedReport: OfficialReportData | null;
  previewHtml: string | null;
  isReportModalOpen: boolean;
  isLoadingReport: boolean;
  isExportingDocx: boolean;
  reportError: string | null;
  isDataReady: boolean;
  generatingMessage: string | null;

  // Actions
  openReportModal: () => void;
  closeReportModal: () => void;
  fetchOfficialReport: (resultId?: string, xaiResult?: any) => Promise<OfficialReportData | null>;
  exportDocx: (outputPath?: string) => Promise<{ success: boolean; output_path?: string; error?: string }>;
}

export const useReportStore = create<ReportStoreState>((set, get) => ({
  selectedReport: null,
  previewHtml: null,
  isReportModalOpen: false,
  isLoadingReport: false,
  isExportingDocx: false,
  reportError: null,
  isDataReady: true,
  generatingMessage: null,

  openReportModal: () => {
    set({
      selectedReport: null,
      previewHtml: null,
      isReportModalOpen: true,
      isDataReady: true,
      generatingMessage: null,
      reportError: null,
    });
    get().fetchOfficialReport();
  },

  closeReportModal: () =>
    set({
      isReportModalOpen: false,
      selectedReport: null,
      previewHtml: null,
      reportError: null,
    }),

  fetchOfficialReport: async (resultId?: string, xaiResult?: any) => {
    const isConnected = useSystemStore.getState().connected;
    if (!isConnected) {
      set({
        isLoadingReport: false,
        reportError: 'Backend desconectado: o processo Python não está respondendo. Verifique o terminal ou reinicie a aplicação.',
        generatingMessage: null,
      });
      return null;
    }

    set({
      isLoadingReport: true,
      reportError: null,
      generatingMessage: 'Processando Parecer Técnico Pericial via SLM Jurista (Qwen3 GGUF)... Isso pode levar alguns segundos.',
    });
    try {
      const municipal = useMunicipalSettingsStore.getState();
      const typography = useReportTypographyStore.getState();

      const res = await xaiService.generateOfficialReport({
        result_id: resultId,
        xai_result: xaiResult,
        municipal_config: {
          cityHall: municipal.cityHall,
          department: municipal.department,
          authorityName: municipal.authorityName,
          authorityRole: municipal.authorityRole,
          registrationNumber: municipal.registrationNumber,
          processPrefix: municipal.processPrefix,
        },
        typography_options: {
          fontFamily: typography.fontFamily,
          fontSize: typography.fontSize,
          lineSpacing: typography.lineSpacing,
          alignment: typography.alignment,
        },
      });

      if (res && res.ready === false) {
        set({
          isDataReady: false,
          generatingMessage:
            res.message ||
            'Os dados de telemetria e fusão neural estão sendo gerados na malha viária.',
          selectedReport: null,
          previewHtml: null,
          isLoadingReport: false,
        });
        return null;
      }

      if (res && res.success && res.report) {
        set({
          isDataReady: true,
          generatingMessage: null,
          selectedReport: res.report,
          previewHtml: res.preview_html || null,
          isLoadingReport: false,
        });
        return res.report;
      }
      throw new Error(res.error || res.message || 'Falha ao sintetizar laudo no backend');
    } catch (e: any) {
      console.warn('Erro ao carregar laudo pericial oficial:', e);
      set({
        isLoadingReport: false,
        reportError: e?.message || 'Erro ao carregar laudo técnico oficial.',
      });
      return null;
    }
  },

  exportDocx: async (outputPath?: string) => {
    const isConnected = useSystemStore.getState().connected;
    if (!isConnected) {
      const err = 'Backend desconectado: o Core Python não está respondendo. Exportação bloqueada.';
      set({ reportError: err });
      return { success: false, error: err };
    }

    const { isDataReady, generatingMessage } = get();
    if (!isDataReady) {
      const msg = generatingMessage || 'Dados de telemetria em processamento. Exportação bloqueada.';
      set({ reportError: msg });
      return { success: false, error: msg };
    }
    set({ isExportingDocx: true, reportError: null });
    try {
      const { selectedReport } = get();
      const municipal = useMunicipalSettingsStore.getState();
      const typography = useReportTypographyStore.getState();

      const res = await xaiService.exportOfficialReportDocx({
        output_path: outputPath,
        report: selectedReport || undefined,
        municipal_config: {
          cityHall: municipal.cityHall,
          department: municipal.department,
          authorityName: municipal.authorityName,
          authorityRole: municipal.authorityRole,
          registrationNumber: municipal.registrationNumber,
          processPrefix: municipal.processPrefix,
        },
        typography_options: {
          fontFamily: typography.fontFamily,
          fontSize: typography.fontSize,
          lineSpacing: typography.lineSpacing,
          alignment: typography.alignment,
        },
      });

      set({ isExportingDocx: false });
      return res;
    } catch (e: any) {
      set({ isExportingDocx: false, reportError: e?.message || 'Erro ao exportar DOCX' });
      return { success: false, error: e?.message || 'Erro ao exportar DOCX' };
    }
  },
}));
