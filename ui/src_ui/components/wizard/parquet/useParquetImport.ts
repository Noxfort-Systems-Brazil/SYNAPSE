// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { useState, useRef } from 'react';
import { useEtlStore } from '../../../stores';
import { systemService } from '../../../services/api';

export function useParquetImport(isOpen: boolean, onClose: () => void) {
  const {
    parquetInspection,
    importProgress,
    setParquetInspection,
    setImportProgress,
    resetEtlState,
  } = useEtlStore();

  const fileInputRef = useRef<HTMLInputElement>(null);

  const [filePath, setFilePath] = useState('');
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [isLoading, setIsLoading] = useState(false);
  const [isBrowsing, setIsBrowsing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const isValidParquetExtension = (path: string) => {
    return path.toLowerCase().trim().endsWith('.parquet');
  };

  const handleBrowseFile = async () => {
    if (isBrowsing) return;
    setIsBrowsing(true);
    setErrorMessage(null);
    try {
      const res = await systemService.pickFile({
        title: 'Selecionar Base Histórica Parquet (.parquet)',
        filter: 'Base Parquet (*.parquet) | *.parquet',
        filterName: 'Base Parquet (*.parquet)',
        extensions: ['parquet'],
      });
      if (res && res.path && !res.cancelled) {
        if (!isValidParquetExtension(res.path)) {
          setErrorMessage('Por favor, selecione um arquivo válido no formato Parquet (.parquet).');
          return;
        }
        setFilePath(res.path);
        await handleInspectParquet(res.path);
      }
    } catch {
      console.warn('[ParquetImportModal] Falha ao invocar seletor de arquivos.');
    } finally {
      setIsBrowsing(false);
    }
  };

  const handleFileInputChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const fileName = file.name;
      if (!isValidParquetExtension(fileName)) {
        setErrorMessage(`O arquivo '${fileName}' não é uma base Parquet válida (.parquet).`);
        e.target.value = '';
        return;
      }
      const path = (file as any).path || fileName;
      setFilePath(path);
      setErrorMessage(null);
      await handleInspectParquet(path);
    }
  };

  const handleInspectParquet = async (pathOverride?: string) => {
    const cleanPath = (typeof pathOverride === 'string' ? pathOverride : filePath).trim();
    if (!cleanPath) return;

    if (!isValidParquetExtension(cleanPath)) {
      setErrorMessage('O arquivo selecionado deve ter a extensão .parquet.');
      return;
    }

    setIsLoading(true);
    setErrorMessage(null);
    try {
      const res = await systemService.inspectParquet(cleanPath);
      if (res?.num_rows !== undefined) {
        setParquetInspection(res);
        setStep(2);
      } else {
        setErrorMessage('Formato Parquet inválido ou arquivo não encontrado.');
      }
    } catch (err: any) {
      setErrorMessage(err?.message || 'Erro ao inspecionar dataset.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleExecuteImport = async () => {
    const cleanPath = filePath.trim();
    if (!cleanPath) return;

    if (!isValidParquetExtension(cleanPath)) {
      setErrorMessage('O arquivo selecionado deve ter a extensão .parquet.');
      return;
    }

    setStep(3);
    setImportProgress({ isImporting: true, progress: 0 });
    await systemService.importParquet(cleanPath);
  };

  const handleModalClose = () => {
    resetEtlState();
    setStep(1);
    setFilePath('');
    onClose();
  };

  return {
    filePath,
    setFilePath,
    step,
    setStep,
    isLoading,
    isBrowsing,
    errorMessage,
    fileInputRef,
    parquetInspection,
    importProgress,
    handleBrowseFile,
    handleFileInputChange,
    handleInspectParquet,
    handleExecuteImport,
    handleModalClose,
  };
}
