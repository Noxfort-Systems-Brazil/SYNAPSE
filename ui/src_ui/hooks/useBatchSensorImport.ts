// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { useState, useCallback } from 'react';
import { sensorService, systemService } from '../services/api';
import { useSensorsStore } from '../stores';
import { BatchPreviewResult, BatchImportResult } from '../types/sensors';
import {
  SAMPLE_SENSOR_MANIFEST_CSV,
  downloadCsvWithPlatformBridge,
  formatCameraConfigCsv,
} from '../utils/batchCsvUtils';

export interface UseBatchSensorImportReturn {
  fileName: string;
  filePath: string;
  csvContent: string;
  isProcessing: boolean;
  previewData: BatchPreviewResult | null;
  importResult: BatchImportResult | null;
  errorMessage: string | null;
  setErrorMessage: (msg: string | null) => void;
  handleFile: (file: File) => void;
  handleFilePath: (path: string) => Promise<void>;
  confirmImport: () => Promise<void>;
  downloadSample: () => Promise<void>;
  downloadExportConfig: () => Promise<void>;
  reset: () => void;
}

/**
 * Encapsulates batch sensor state management, IPC calls, and I/O orchestration (SOLID: SRP & DIP).
 */
export function useBatchSensorImport(): UseBatchSensorImportReturn {
  const setSources = useSensorsStore((s) => s.setSources);

  const [csvContent, setCsvContent] = useState<string>('');
  const [filePath, setFilePath] = useState<string>('');
  const [fileName, setFileName] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [previewData, setPreviewData] = useState<BatchPreviewResult | null>(null);
  const [importResult, setImportResult] = useState<BatchImportResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const reset = useCallback(() => {
    setCsvContent('');
    setFilePath('');
    setFileName('');
    setPreviewData(null);
    setImportResult(null);
    setErrorMessage(null);
    setIsProcessing(false);
  }, []);

  const downloadSample = useCallback(async () => {
    try {
      await downloadCsvWithPlatformBridge(
        'modelo_sensores_manifesto.csv',
        SAMPLE_SENSOR_MANIFEST_CSV,
        'Salvar Modelo CSV de Sensores'
      );
    } catch (err: any) {
      setErrorMessage(err?.message || 'Falha ao baixar modelo CSV.');
    }
  }, []);

  const downloadExportConfig = useCallback(async () => {
    if (!importResult || !importResult.items || importResult.items.length === 0) return;
    const localItems = importResult.items.filter((item) => item.type === 'local');
    if (localItems.length === 0) {
      setErrorMessage('Nenhum sensor local no lote para exportação de URLs de envio.');
      return;
    }
    try {
      const outputCsv = formatCameraConfigCsv(importResult.items);
      await downloadCsvWithPlatformBridge(
        'config_cameras_locais.csv',
        outputCsv,
        'Salvar Configuração das Câmeras Locais'
      );
    } catch (err: any) {
      setErrorMessage(err?.message || 'Falha ao exportar configurações CSV.');
    }
  }, [importResult]);

  const handleFile = useCallback((file: File) => {
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setErrorMessage('Por favor, selecione um arquivo com extensão .csv');
      return;
    }

    setFileName(file.name);
    setFilePath('');
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

  const handleFilePath = useCallback(async (path: string) => {
    if (!path.toLowerCase().endsWith('.csv')) {
      setErrorMessage('Por favor, selecione um arquivo com extensão .csv');
      return;
    }
    const cleanName = path.split(/[/\\]/).pop() || path;
    setFileName(cleanName);
    setFilePath(path);
    setCsvContent('');
    setIsProcessing(true);
    setErrorMessage(null);
    setImportResult(null);

    try {
      const preview = await sensorService.previewBatchSources(undefined, path);
      setPreviewData(preview);
    } catch (err: any) {
      setErrorMessage(err?.message || 'Falha ao processar e validar o arquivo CSV.');
    } finally {
      setIsProcessing(false);
    }
  }, []);

  const confirmImport = useCallback(async () => {
    if (!csvContent && !filePath) return;
    setIsProcessing(true);
    setErrorMessage(null);

    try {
      const netInfo: any = await systemService.getNetworkInfo().catch(() => ({}));
      const host = netInfo?.local_ip || '127.0.0.1';
      const port = netInfo?.gateway_port || 8081;

      const result = await sensorService.importBatchSources(
        csvContent || undefined,
        host,
        port,
        filePath || undefined
      );
      setImportResult(result);

      // Refresh stores
      const freshSources = await sensorService.getSources();
      setSources(freshSources);
    } catch (err: any) {
      setErrorMessage(err?.message || 'Falha ao importar sensores em lote.');
    } finally {
      setIsProcessing(false);
    }
  }, [csvContent, filePath, setSources]);

  return {
    fileName,
    filePath,
    csvContent,
    isProcessing,
    previewData,
    importResult,
    errorMessage,
    setErrorMessage,
    handleFile,
    handleFilePath,
    confirmImport,
    downloadSample,
    downloadExportConfig,
    reset,
  };
}
