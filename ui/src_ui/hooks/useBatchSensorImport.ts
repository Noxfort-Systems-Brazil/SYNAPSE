// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { useState, useCallback } from 'react';
import { sensorService, systemService } from '../services/api';
import { useSensorsStore } from '../stores';
import { BatchPreviewResult, BatchImportResult } from '../types/sensors';
import {
  SAMPLE_SENSOR_MANIFEST_CSV,
  triggerBlobDownload,
  formatCameraConfigCsv,
} from '../utils/batchCsvUtils';

export interface UseBatchSensorImportReturn {
  fileName: string;
  csvContent: string;
  isProcessing: boolean;
  previewData: BatchPreviewResult | null;
  importResult: BatchImportResult | null;
  errorMessage: string | null;
  setErrorMessage: (msg: string | null) => void;
  handleFile: (file: File) => void;
  confirmImport: () => Promise<void>;
  downloadSample: () => void;
  downloadExportConfig: () => void;
  reset: () => void;
}

/**
 * Encapsulates batch sensor state management, IPC calls, and I/O orchestration (SOLID: SRP & DIP).
 */
export function useBatchSensorImport(): UseBatchSensorImportReturn {
  const setSources = useSensorsStore((s) => s.setSources);

  const [csvContent, setCsvContent] = useState<string>('');
  const [fileName, setFileName] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [previewData, setPreviewData] = useState<BatchPreviewResult | null>(null);
  const [importResult, setImportResult] = useState<BatchImportResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const reset = useCallback(() => {
    setCsvContent('');
    setFileName('');
    setPreviewData(null);
    setImportResult(null);
    setErrorMessage(null);
    setIsProcessing(false);
  }, []);

  const downloadSample = useCallback(() => {
    triggerBlobDownload('sample_sensors_manifest.csv', SAMPLE_SENSOR_MANIFEST_CSV);
  }, []);

  const downloadExportConfig = useCallback(() => {
    if (!importResult || !importResult.items || importResult.items.length === 0) return;
    const outputCsv = formatCameraConfigCsv(importResult.items);
    triggerBlobDownload('config_cameras.csv', outputCsv);
  }, [importResult]);

  const handleFile = useCallback((file: File) => {
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setErrorMessage('Por favor, selecione um arquivo com extensão .csv');
      return;
    }

    setFileName(file.name);
    setIsProcessing(true);
    setErrorMessage(null);
    setImportResult(null);

    const reader = new FileReader();
    reader.onload = async (event) => {
      const text = (event.target?.result as string) || '';
      setCsvContent(text);

      try {
        const preview = await sensorService.previewBatchSources(text);
        setPreviewData(preview);
      } catch (err: any) {
        setErrorMessage(err?.message || 'Falha ao processar e validar o arquivo CSV.');
      } finally {
        setIsProcessing(false);
      }
    };

    reader.onerror = () => {
      setErrorMessage('Erro ao ler o arquivo selecionado.');
      setIsProcessing(false);
    };

    reader.readAsText(file);
  }, []);

  const confirmImport = useCallback(async () => {
    if (!csvContent) return;
    setIsProcessing(true);
    setErrorMessage(null);

    try {
      const netInfo: any = await systemService.getNetworkInfo().catch(() => ({}));
      const host = netInfo?.local_ip || '127.0.0.1';
      const port = netInfo?.gateway_port || 8081;

      const result = await sensorService.importBatchSources(csvContent, host, port);
      setImportResult(result);

      // Refresh stores
      const freshSources = await sensorService.getSources();
      setSources(freshSources);
    } catch (err: any) {
      setErrorMessage(err?.message || 'Falha ao importar sensores em lote.');
    } finally {
      setIsProcessing(false);
    }
  }, [csvContent, setSources]);

  return {
    fileName,
    csvContent,
    isProcessing,
    previewData,
    importResult,
    errorMessage,
    setErrorMessage,
    handleFile,
    confirmImport,
    downloadSample,
    downloadExportConfig,
    reset,
  };
}
