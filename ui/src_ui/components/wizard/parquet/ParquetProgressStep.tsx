// SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
// Copyright (C) 2026 Noxfort Systems
//
// File: ui/src_ui/components/wizard/parquet/ParquetProgressStep.tsx
// Author: Gabriel Moraes
// Date: 2026-09-14

import React from 'react';
import { Database } from 'lucide-react';

interface ImportProgressData {
  isImporting: boolean;
  progress: number;
  status?: string;
}

interface ParquetProgressStepProps {
  importProgress: ImportProgressData;
}

export const ParquetProgressStep: React.FC<ParquetProgressStepProps> = ({
  importProgress,
}) => {
  return (
    <div className="space-y-4 text-xs text-center py-6">
      <div className="w-12 h-12 rounded-2xl bg-accent-cyan/10 border border-accent-cyan/30 flex items-center justify-center mx-auto mb-2 animate-bounce">
        <Database className="w-6 h-6 text-accent-cyan" />
      </div>
      <h3 className="text-sm font-bold text-slate-900 dark:text-white">
        Ingestão de Dados Históricos em Andamento...
      </h3>

      <div className="w-full h-3 bg-slate-200 dark:bg-background rounded-full overflow-hidden border border-border">
        <div
          className="h-full bg-gradient-to-r from-primary-500 to-accent-cyan transition-all duration-300"
          style={{ width: `${importProgress.progress}%` }}
        />
      </div>
      <span className="text-xs font-mono text-slate-600 dark:text-slate-400 font-semibold">
        {importProgress.progress}% Concluído{' '}
        {importProgress.status ? `(${importProgress.status})` : ''}
      </span>
    </div>
  );
};
