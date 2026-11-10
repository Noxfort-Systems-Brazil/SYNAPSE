import React, { useRef, useState } from 'react';
import { Upload, Download } from 'lucide-react';
import { systemService } from '../../../services/api';
import { isTauriEnvironment } from '../../../services/transport';

interface BatchDropzoneProps {
  fileName: string;
  onFileSelected: (file: File) => void;
  onFilePathSelected?: (path: string) => void;
  onDownloadSample: () => void | Promise<void>;
  onError: (msg: string) => void;
}

export const BatchDropzone: React.FC<BatchDropzoneProps> = ({
  fileName,
  onFileSelected,
  onFilePathSelected,
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
      if (!file.name.toLowerCase().endsWith('.csv')) {
        onError('Por favor, selecione um arquivo com extensão .csv');
        return;
      }
      onFileSelected(file);
    }
  };

  const handleClick = async () => {
    if (isTauriEnvironment() && onFilePathSelected) {
      try {
        const res = await systemService.pickFile({
          title: 'Selecionar Planilha de Sensores (.csv)',
          filter: 'Planilhas CSV (*.csv) | *.csv',
          filterName: 'Planilhas CSV (*.csv)',
          extensions: ['csv'],
        });
        if (res && res.path && !res.cancelled) {
          if (!res.path.toLowerCase().endsWith('.csv')) {
            onError('Por favor, selecione um arquivo com extensão .csv');
            return;
          }
          onFilePathSelected(res.path);
        }
      } catch (err) {
        console.warn('[BatchDropzone] Falha no seletor nativo, usando fallback HTML:', err);
        fileInputRef.current?.click();
      }
    } else {
      fileInputRef.current?.click();
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
          Arquivo de Manifesto (.csv)
        </span>
        <button
          type="button"
          onClick={onDownloadSample}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-primary-500/30 bg-primary-500/10 hover:bg-primary-500/20 text-primary-600 dark:text-primary-400 font-semibold text-xs transition-all shadow-xs hover:shadow-primary-500/10 cursor-pointer active:scale-95"
          title="Baixar arquivo modelo .CSV com as colunas: name, type, id, address"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Baixar Modelo .CSV</span>
        </button>
      </div>

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={handleClick}
        className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all ${
          isDragging
            ? 'border-primary-500 bg-primary-500/10'
            : 'border-border/80 hover:border-primary-500/60 bg-surface/50 hover:bg-surfaceHover/50'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,text/csv,application/vnd.ms-excel"
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

      {/* Helper callout for template */}
      <div className="flex items-center justify-between px-3.5 py-2.5 bg-surfaceHover/60 rounded-xl border border-border/80 text-xs text-slate-600 dark:text-slate-400">
        <div className="flex items-center gap-2">
          <Download className="w-4 h-4 text-primary-500 shrink-0" />
          <span>Não possui uma planilha pronta?</span>
        </div>
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onDownloadSample();
          }}
          className="text-xs text-primary-600 dark:text-primary-400 font-semibold hover:underline cursor-pointer shrink-0"
        >
          Baixar modelo .CSV base &rarr;
        </button>
      </div>
    </div>
  );
};
