// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { Upload, Trash2, Image as ImageIcon } from 'lucide-react';

interface MunicipalLogoUploaderProps {
  logoPreview: string | null;
  fileInputRef: React.RefObject<HTMLInputElement>;
  onUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
  onRemove: () => void;
}

export const MunicipalLogoUploader: React.FC<MunicipalLogoUploaderProps> = ({
  logoPreview,
  fileInputRef,
  onUpload,
  onRemove,
}) => {
  return (
    <div className="p-4 bg-slate-100 dark:bg-slate-900 rounded-2xl border border-slate-300 dark:border-slate-700 space-y-3 shadow-xs">
      <label className="text-xs font-bold text-slate-950 dark:text-slate-100 block uppercase tracking-wide">
        Logotipo Oficial da Prefeitura / Brasão de Armas
      </label>

      <div className="flex items-center gap-4">
        <div className="w-20 h-20 rounded-xl border-2 border-dashed border-slate-400 dark:border-slate-600 bg-white dark:bg-slate-950 flex items-center justify-center overflow-hidden shadow-inner">
          {logoPreview ? (
            <img src={logoPreview} alt="Brasão da Prefeitura" className="w-full h-full object-contain p-1" />
          ) : (
            <ImageIcon className="w-8 h-8 text-slate-500 opacity-80" />
          )}
        </div>

        <div className="space-y-2 flex-1">
          <input
            type="file"
            ref={fileInputRef}
            onChange={onUpload}
            accept="image/png, image/jpeg, image/svg+xml"
            className="hidden"
          />

          <div className="flex items-center gap-2">
            <button
              onClick={() => fileInputRef.current?.click()}
              className="px-3.5 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 dark:bg-primary-600 dark:hover:bg-primary-500 text-white text-xs font-bold transition-all flex items-center gap-1.5 shadow-xs"
            >
              <Upload className="w-3.5 h-3.5" />
              <span>Carregar Imagem do Brasão</span>
            </button>

            {logoPreview && (
              <button
                onClick={onRemove}
                className="px-2.5 py-1.5 rounded-lg border border-rose-300 dark:border-rose-800 bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400 hover:bg-rose-100 text-xs font-bold transition-all flex items-center gap-1"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Remover</span>
              </button>
            )}
          </div>
          <p className="text-[11px] text-slate-600 dark:text-slate-400 font-medium">
            Formatos aceitos: PNG, JPG, SVG (recomendado arquivo de alta resolução com fundo transparente).
          </p>
        </div>
      </div>
    </div>
  );
};
