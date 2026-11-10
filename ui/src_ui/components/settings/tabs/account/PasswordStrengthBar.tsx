// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { useTranslation } from 'react-i18next';
import { PasswordStrength } from '../../../../utils/passwordPolicy';

interface PasswordStrengthBarProps {
  score: number;
  strength: PasswordStrength;
  hasContent: boolean;
}

export const PasswordStrengthBar: React.FC<PasswordStrengthBarProps> = ({
  score,
  strength,
  hasContent,
}) => {
  const { t } = useTranslation();

  if (!hasContent) return null;

  const getBarColorAndWidth = () => {
    if (score <= 1) return 'w-1/4 bg-rose-500';
    if (score === 2) return 'w-2/4 bg-amber-500';
    if (score === 3) return 'w-3/4 bg-blue-500';
    return 'w-full bg-emerald-500';
  };

  const getStrengthLabel = () => {
    switch (strength) {
      case 'weak':
        return { label: t('security.strengthWeak'), color: 'text-rose-500' };
      case 'medium':
        return { label: t('security.strengthMedium'), color: 'text-amber-500' };
      case 'strong':
        return { label: t('security.strengthStrong'), color: 'text-blue-500' };
      case 'veryStrong':
        return { label: t('security.strengthVeryStrong'), color: 'text-emerald-500' };
      default:
        return { label: '', color: '' };
    }
  };

  const strengthInfo = getStrengthLabel();

  return (
    <div className="space-y-1 mt-1">
      <div className="flex justify-end">
        <span className={`text-[10px] font-bold ${strengthInfo.color}`}>
          {strengthInfo.label}
        </span>
      </div>
      <div className="w-full h-1 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
        <div className={`h-full transition-all duration-300 ${getBarColorAndWidth()}`} />
      </div>
    </div>
  );
};
