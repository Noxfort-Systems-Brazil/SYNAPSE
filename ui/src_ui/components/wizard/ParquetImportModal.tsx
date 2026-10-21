// SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
// Copyright (C) 2026 Noxfort Systems
//
// File: ui/src_ui/components/wizard/ParquetImportModal.tsx
// Author: Gabriel Moraes
// Date: 2026-08-29

import React from 'react';
import { useTranslation } from 'react-i18next';
import { X, Database, CheckCircle2, ArrowRight } from 'lucide-react';
import {
  useParquetImport,
  ParquetSelectStep,
  ParquetInspectStep,
  ParquetProgressStep,
} from './parquet';

interface ParquetImportModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const ParquetImportModal: React.FC<ParquetImportModalProps> = ({ isOpen, onClose }) => {
  const { t } = useTranslation();
  const etl = useParquetImport(isOpen, onClose);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in select-none">
      <div className="w-full max-w-2xl glass-panel bg-surface p-6 rounded-2xl shadow-2xl border border-border space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border/80 pb-4">
          <h2 className="text-base font-bold text-slate-900 dark:text-white tracking-tight flex items-center gap-2">
            <Database className="w-5 h-5 text-accent-cyan" />
            <span>Assistente de Importação Parquet</span>
          </h2>
          <button
            onClick={etl.handleModalClose}
            className="p-1.5 rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-surfaceHover transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Hidden file input for web fallback */}
        <input
          ref={etl.fileInputRef}
          type="file"
          accept=".parquet"
          onChange={etl.handleFileInputChange}
          className="hidden"
        />

        {/* STEP 1: Path Selection */}
        {etl.step === 1 && (
          <ParquetSelectStep
            filePath={etl.filePath}
            setFilePath={etl.setFilePath}
            isBrowsing={etl.isBrowsing}
            onBrowseFile={etl.handleBrowseFile}
            errorMessage={etl.errorMessage}
          />
        )}

        {/* STEP 2: Dataset Inspection */}
        {etl.step === 2 && etl.parquetInspection && (
          <ParquetInspectStep parquetInspection={etl.parquetInspection} />
        )}

        {/* STEP 3: Ingestion Progress */}
        {etl.step === 3 && <ParquetProgressStep importProgress={etl.importProgress} />}

        {/* Footer */}
        <div className="flex items-center justify-end gap-2 border-t border-border/80 pt-4">
          <button
            onClick={etl.handleModalClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors"
          >
            {t('settings.cancel')}
          </button>

          {etl.step === 1 && (
            <button
              onClick={() => etl.handleInspectParquet()}
              disabled={!etl.filePath.trim() || etl.isLoading}
              className="px-5 py-2 rounded-xl bg-primary-600 hover:bg-primary-500 disabled:opacity-50 text-white text-xs font-bold shadow-md shadow-primary-600/20 transition-all flex items-center gap-1.5"
            >
              {etl.isLoading ? (
                <span className="animate-spin text-white">⏳</span>
              ) : (
                <ArrowRight className="w-4 h-4" />
              )}
              <span>{etl.isLoading ? 'Inspecionando...' : 'Inspecionar Dataset'}</span>
            </button>
          )}

          {etl.step === 2 && (
            <button
              onClick={etl.handleExecuteImport}
              className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-md shadow-emerald-600/30 transition-all flex items-center gap-1.5"
            >
              <span>Iniciar Ingestão no Banco</span>
              <CheckCircle2 className="w-4 h-4" />
            </button>
          )}

          {etl.step === 3 && (
            <button
              onClick={etl.handleModalClose}
              disabled={etl.importProgress.progress < 100}
              className="px-5 py-2 rounded-xl bg-primary-600 hover:bg-primary-500 disabled:opacity-50 text-white text-xs font-bold transition-all"
            >
              Concluir
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
