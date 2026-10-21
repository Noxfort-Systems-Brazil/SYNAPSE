// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { X, Layers, AlertTriangle, RefreshCw, ArrowRight } from 'lucide-react';
import { useBatchSensorImport } from '../../hooks/useBatchSensorImport';
import { BatchDropzone } from './batch/BatchDropzone';
import { BatchPreviewTable } from './batch/BatchPreviewTable';
import { BatchSuccessView } from './batch/BatchSuccessView';

interface BatchImportModalProps {
  isOpen: boolean;
  onClose: () => void;
}

/**
 * Pure Coordinator Modal for Batch Sensor Ingestion (SOLID compliant: SRP & DIP).
 * Delegating state to useBatchSensorImport and views to specialized subcomponents.
 */
export const BatchImportModal: React.FC<BatchImportModalProps> = ({ isOpen, onClose }) => {
  const {
    fileName,
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
  } = useBatchSensorImport();

  if (!isOpen) return null;

  const handleClose = () => {
    reset();
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-md p-4 animate-in fade-in select-none">
      <div className="w-full max-w-4xl glass-panel bg-surface p-6 rounded-2xl shadow-2xl border border-border flex flex-col max-h-[90vh]">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-border/80 pb-4 flex-shrink-0">
          <div>
            <h2 className="text-base font-bold text-slate-900 dark:text-white tracking-tight flex items-center gap-2">
              <Layers className="w-5 h-5 text-primary-500 dark:text-primary-400" />
              <span>Importação em Lote de Sensores Locais (CSV)</span>
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Provisione dezenas ou centenas de câmeras/laços a partir de um arquivo com colunas{' '}
              <code className="px-1 py-0.5 bg-surfaceHover rounded font-mono text-[11px] text-primary-500">
                name,location
              </code>
            </p>
          </div>
          <button
            onClick={handleClose}
            className="p-1.5 rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-surfaceHover transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto py-4 space-y-4 pr-1">
          {errorMessage && (
            <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-xs text-rose-600 dark:text-rose-400 flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* 1. File Upload Dropzone */}
          {!importResult && (
            <BatchDropzone
              fileName={fileName}
              onFileSelected={handleFile}
              onDownloadSample={downloadSample}
              onError={(msg) => setErrorMessage(msg)}
            />
          )}

          {/* 2. Loading State */}
          {isProcessing && (
            <div className="flex items-center justify-center gap-2 py-6 text-xs text-slate-500">
              <RefreshCw className="w-4 h-4 animate-spin text-primary-500" />
              <span>Validando sensores com a topologia viária...</span>
            </div>
          )}

          {/* 3. Pre-flight Dry-Run Preview Table */}
          {previewData && !importResult && !isProcessing && (
            <BatchPreviewTable previewData={previewData} />
          )}

          {/* 4. Success View & Export Download */}
          {importResult && (
            <BatchSuccessView
              importResult={importResult}
              onDownloadConfig={downloadExportConfig}
            />
          )}
        </div>

        {/* Modal Footer Actions */}
        <div className="flex items-center justify-between border-t border-border/80 pt-4 flex-shrink-0">
          <button
            type="button"
            onClick={handleClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-surfaceHover transition-colors cursor-pointer"
          >
            {importResult ? 'Concluir' : 'Cancelar'}
          </button>

          {!importResult && previewData && previewData.valid_count > 0 && (
            <button
              type="button"
              disabled={isProcessing}
              onClick={confirmImport}
              className="flex items-center gap-2 px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white rounded-xl text-xs font-semibold shadow-lg shadow-primary-500/20 transition-all cursor-pointer"
            >
              <span>Confirmar e Cadastrar {previewData.valid_count} Sensores</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
