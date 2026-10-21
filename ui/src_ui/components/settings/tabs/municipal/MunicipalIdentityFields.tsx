// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';

interface MunicipalFormState {
  cityHall: string;
  department: string;
  authorityName: string;
  authorityRole: string;
  registrationNumber: string;
  processPrefix: string;
}

interface MunicipalIdentityFieldsProps {
  form: MunicipalFormState;
  onChange: (updates: Partial<MunicipalFormState>) => void;
}

export const MunicipalIdentityFields: React.FC<MunicipalIdentityFieldsProps> = ({
  form,
  onChange,
}) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
      <div className="space-y-1 sm:col-span-2">
        <label className="font-bold text-slate-950 dark:text-slate-100 block">
          Nome do Município / Prefeitura
        </label>
        <input
          type="text"
          value={form.cityHall}
          onChange={(e) => onChange({ cityHall: e.target.value })}
          placeholder="Ex: PREFEITURA DO MUNICÍPIO DE SÃO PAULO"
          className="w-full px-3.5 py-2.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-950 dark:text-white text-xs font-semibold focus:ring-2 focus:ring-slate-900 dark:focus:ring-primary-500 outline-hidden shadow-xs"
        />
      </div>

      <div className="space-y-1 sm:col-span-2">
        <label className="font-bold text-slate-950 dark:text-slate-100 block">
          Secretaria Demandante
        </label>
        <input
          type="text"
          value={form.department}
          onChange={(e) => onChange({ department: e.target.value })}
          placeholder="Ex: SECRETARIA MUNICIPAL DE MOBILIDADE URBANA E TRÂNSITO (SMT)"
          className="w-full px-3.5 py-2.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-950 dark:text-white text-xs font-semibold focus:ring-2 focus:ring-slate-900 dark:focus:ring-primary-500 outline-hidden shadow-xs"
        />
      </div>

      <div className="space-y-1">
        <label className="font-bold text-slate-950 dark:text-slate-100 block">
          Nome da Autoridade / Responsável
        </label>
        <input
          type="text"
          value={form.authorityName}
          onChange={(e) => onChange({ authorityName: e.target.value })}
          placeholder="Ex: Gabriel Moraes"
          className="w-full px-3.5 py-2.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-950 dark:text-white text-xs font-semibold focus:ring-2 focus:ring-slate-900 dark:focus:ring-primary-500 outline-hidden shadow-xs"
        />
      </div>

      <div className="space-y-1">
        <label className="font-bold text-slate-950 dark:text-slate-100 block">
          Cargo / Função Oficial
        </label>
        <input
          type="text"
          value={form.authorityRole}
          onChange={(e) => onChange({ authorityRole: e.target.value })}
          placeholder="Ex: Autoridade Municipal de Trânsito / Secretário de Mobilidade"
          className="w-full px-3.5 py-2.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-950 dark:text-white text-xs font-semibold focus:ring-2 focus:ring-slate-900 dark:focus:ring-primary-500 outline-hidden shadow-xs"
        />
      </div>

      <div className="space-y-1">
        <label className="font-bold text-slate-950 dark:text-slate-100 block">
          Matrícula Funcional / Portaria de Nomeação
        </label>
        <input
          type="text"
          value={form.registrationNumber}
          onChange={(e) => onChange({ registrationNumber: e.target.value })}
          placeholder="Ex: Matrícula Funcional nº 84.102-3 • Portaria SMT nº 142/2025"
          className="w-full px-3.5 py-2.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-950 dark:text-white text-xs font-mono font-semibold focus:ring-2 focus:ring-slate-900 dark:focus:ring-primary-500 outline-hidden shadow-xs"
        />
      </div>

      <div className="space-y-1">
        <label className="font-bold text-slate-950 dark:text-slate-100 block">
          Prefixo do Processo Administrativo
        </label>
        <input
          type="text"
          value={form.processPrefix}
          onChange={(e) => onChange({ processPrefix: e.target.value })}
          placeholder="Ex: PA-SMT-2026/"
          className="w-full px-3.5 py-2.5 rounded-xl bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-700 text-slate-950 dark:text-white text-xs font-mono font-semibold focus:ring-2 focus:ring-slate-900 dark:focus:ring-primary-500 outline-hidden shadow-xs"
        />
      </div>
    </div>
  );
};
