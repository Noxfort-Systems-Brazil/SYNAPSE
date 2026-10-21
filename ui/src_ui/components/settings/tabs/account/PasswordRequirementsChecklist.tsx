// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { useTranslation } from 'react-i18next';
import { Check, ShieldCheck, ShieldAlert } from 'lucide-react';
import { PasswordRequirement } from '../../../../utils/passwordPolicy';

interface PasswordRequirementsChecklistProps {
  requirements: PasswordRequirement[];
  allMet: boolean;
}

export const PasswordRequirementsChecklist: React.FC<PasswordRequirementsChecklistProps> = ({
  requirements,
  allMet,
}) => {
  const { t } = useTranslation();

  return (
    <div className="p-3 rounded-xl bg-background/50 border border-border/60 space-y-2">
      <div className="flex items-center gap-1.5 text-[11px] font-bold text-slate-700 dark:text-slate-300">
        {allMet ? (
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
        ) : (
          <ShieldAlert className="w-3.5 h-3.5 text-amber-500" />
        )}
        <span>{t('security.passwordRequirements', 'Critérios Obrigatórios de Segurança:')}</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-4 gap-y-1.5 text-[10px]">
        {requirements.map((req) => (
          <div
            key={req.id}
            className={`flex items-center gap-1.5 transition-colors ${
              req.isMet
                ? 'text-emerald-600 dark:text-emerald-400 font-medium'
                : 'text-slate-500 dark:text-slate-400'
            }`}
          >
            {req.isMet ? (
              <Check className="w-3 h-3 text-emerald-500 shrink-0" />
            ) : (
              <div className="w-3 h-3 flex items-center justify-center shrink-0">
                <div className="w-1.5 h-1.5 rounded-full bg-slate-300 dark:bg-slate-600" />
              </div>
            )}
            <span>{t(req.labelKey, req.fallbackLabel)}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
