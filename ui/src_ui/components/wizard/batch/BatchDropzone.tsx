// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React, { useRef, useState } from 'react';
import { Upload, Download } from 'lucide-react';

interface BatchDropzoneProps {
  fileName: string;
  onFileSelected: (file: File) => void;
  onDownloadSample: () => void;
  onError: (msg: string) => void;
}

export const BatchDropzone: React.FC<BatchDropzoneProps> = ({
  fileName,
  onFileSelected,
  onDownloadSample,
  onError,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.csv')) {
      onError('Por favor, selecione um arquivo com extensão .csv');
      return;
    }
    onFileSelected(file);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      onFileSelected(file);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
          Arquivo de Manifesto (.csv)
        </span>
        <button
          type="button"
          onClick={onDownloadSample}
          className="flex items-center gap-1.5 text-xs text-primary-500 hover:text-primary-600 dark:hover:text-primary-400 transition-colors cursor-pointer"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Baixar Modelo CSV (name,location)</span>
        </button>
      </div>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all ${
          isDragging
            ? 'border-primary-500 bg-primary-500/10'
            : 'border-border/80 hover:border-primary-500/60 bg-surface/50 hover:bg-surfaceHover/50'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv"
          className="hidden"
          onChange={handleInputChange}
        />
        <Upload className="w-8 h-8 mx-auto mb-2 text-slate-400 dark:text-slate-500" />
        <p className="text-xs font-medium text-slate-700 dark:text-slate-200">
          {fileName ? (
            <span className="text-primary-500 font-semibold">{fileName}</span>
          ) : (
            'Clique para selecionar ou arraste o arquivo .csv aqui'
          )}
        </p>
        <p className="text-[11px] text-slate-400 dark:text-slate-500 mt-1">
          Formatos aceitos: delimitados por vírgula (,) ou ponto-e-vírgula (;)
        </p>
      </div>
    </div>
  );
};
