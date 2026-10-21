// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { Landmark, Check, RefreshCw } from 'lucide-react';
import {
  useMunicipalForm,
  MunicipalLogoUploader,
  MunicipalIdentityFields,
} from './municipal';

export const MunicipalSettingsTab: React.FC = () => {
  const {
    form,
    setForm,
    logoPreview,
    savedSuccess,
    fileInputRef,
    handleLogoUpload,
    handleRemoveLogo,
    handleSave,
    handleReset,
  } = useMunicipalForm();

  return (
    <div className="space-y-5 select-none animate-in fade-in">
      <div className="flex items-center justify-between border-b border-slate-300 dark:border-slate-700 pb-3">
        <div>
          <h3 className="text-sm font-bold text-slate-950 dark:text-white flex items-center gap-2">
            <Landmark className="w-4 h-4 text-primary-600 dark:text-primary-400" />
            Identidade Municipal & Secretaria Demandante
          </h3>
          <p className="text-xs text-slate-700 dark:text-slate-300 mt-0.5 font-medium">
            Personalize a prefeitura, secretaria demandante, autoridade responsável e logotipo oficial dos relatórios.
          </p>
        </div>

        <button
          onClick={handleReset}
          className="px-2.5 py-1.5 text-[11px] font-bold text-slate-800 dark:text-slate-200 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg transition-all flex items-center gap-1.5"
          title="Restaurar dados padrão"
        >
          <RefreshCw className="w-3.5 h-3.5 text-slate-700 dark:text-slate-300" />
          <span>Restaurar Padrão</span>
        </button>
      </div>

      {/* Card de Upload do Brasão / Logotipo Oficial */}
      <MunicipalLogoUploader
        logoPreview={logoPreview}
        fileInputRef={fileInputRef}
        onUpload={handleLogoUpload}
        onRemove={handleRemoveLogo}
      />

      {/* Formulário de Identificação Institucional da Secretaria Demandante */}
      <MunicipalIdentityFields
        form={form}
        onChange={(updates) => setForm((prev) => ({ ...prev, ...updates }))}
      />

      {/* Salvar Configurações */}
      <div className="flex items-center justify-end pt-4 border-t border-slate-300 dark:border-slate-700">
        <button
          onClick={handleSave}
          className="px-6 py-2.5 rounded-xl bg-slate-950 hover:bg-slate-800 dark:bg-primary-600 dark:hover:bg-primary-500 text-white text-xs font-bold transition-all flex items-center gap-2 shadow-md"
        >
          {savedSuccess ? (
            <>
              <Check className="w-4 h-4 text-emerald-400" />
              <span>Configurações Salvas com Sucesso!</span>
            </>
          ) : (
            <span>Salvar Alterações</span>
          )}
        </button>
      </div>
    </div>
  );
};
