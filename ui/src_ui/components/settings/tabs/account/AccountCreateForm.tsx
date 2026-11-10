// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  UserPlus,
  User,
  Lock,
  Eye,
  EyeOff,
  ShieldCheck,
  Loader2,
} from 'lucide-react';
import {
  PasswordRequirement,
  PasswordValidationResult,
} from '../../../../utils/passwordPolicy';
import { PasswordStrengthBar } from './PasswordStrengthBar';
import { PasswordRequirementsChecklist } from './PasswordRequirementsChecklist';

export interface AccountCreateFormProps {
  username: string;
  setUsername: (val: string) => void;
  password: string;
  setPassword: (val: string) => void;
  confirmPassword: string;
  setConfirmPassword: (val: string) => void;
  role: 'OPERATOR' | 'SUPERUSER';
  setRole: (val: 'OPERATOR' | 'SUPERUSER') => void;
  validation: PasswordValidationResult;
  requirements: PasswordRequirement[];
  passwordsMatch: boolean;
  canSubmit: boolean;
  isSubmitting: boolean;
  onSubmit: (e: React.FormEvent) => Promise<void>;
}

export const AccountCreateForm: React.FC<AccountCreateFormProps> = ({
  username,
  setUsername,
  password,
  setPassword,
  confirmPassword,
  setConfirmPassword,
  role,
  setRole,
  validation,
  requirements,
  passwordsMatch,
  canSubmit,
  isSubmitting,
  onSubmit,
}) => {
  const { t } = useTranslation();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  return (
    <div className="p-5 rounded-2xl bg-surfaceElevated border border-border shadow-sm space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-bold text-slate-900 dark:text-white flex items-center gap-2 text-sm">
          <UserPlus className="w-4 h-4 text-primary-500" />
          <span>{t('accounts.addNewAccount')}</span>
        </h3>
        <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400 flex items-center gap-1">
          <ShieldCheck className="w-3.5 h-3.5 text-primary-500" />
          {t('security.standardProtected')}
        </span>
      </div>

      <form onSubmit={onSubmit} className="space-y-4">
        {/* Username & Role Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="space-y-1">
            <label className="text-[11px] font-semibold text-slate-700 dark:text-slate-300">
              {t('security.username')} *
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-2.5 flex items-center pointer-events-none text-slate-400">
                <User className="w-3.5 h-3.5" />
              </div>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="ex.: operador_turno1"
                className="w-full pl-8 pr-3 py-1.5 text-xs rounded-lg bg-background border border-border focus:border-primary-500 outline-none text-slate-900 dark:text-white transition-colors"
                required
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-semibold text-slate-700 dark:text-slate-300">
              {t('accounts.accessLevel')}
            </label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value as 'OPERATOR' | 'SUPERUSER')}
              className="w-full px-3 py-1.5 text-xs rounded-lg bg-background border border-border focus:border-primary-500 outline-none text-slate-900 dark:text-white cursor-pointer transition-colors"
            >
              <option value="OPERATOR">
                {t('accounts.operator')}
              </option>
              <option value="SUPERUSER">
                {t('accounts.superuser')}
              </option>
            </select>
          </div>
        </div>

        {/* Password & Confirm Password Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="space-y-1">
            <label className="text-[11px] font-semibold text-slate-700 dark:text-slate-300">
              {t('security.password')} *
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-2.5 flex items-center pointer-events-none text-slate-400">
                <Lock className="w-3.5 h-3.5" />
              </div>
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-8 pr-8 py-1.5 text-xs rounded-lg bg-background border border-border focus:border-primary-500 outline-none text-slate-900 dark:text-white transition-colors"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 pr-2.5 flex items-center text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
                title={showPassword ? 'Ocultar senha' : 'Exibir senha'}
              >
                {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
              </button>
            </div>
            {/* SRP Subcomponent: PasswordStrengthBar */}
            <PasswordStrengthBar
              score={validation.strengthScore}
              strength={validation.strength}
              hasContent={password.length > 0}
            />
          </div>

          <div className="space-y-1">
            <label className="text-[11px] font-semibold text-slate-700 dark:text-slate-300">
              {t('security.confirmPassword')} *
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-2.5 flex items-center pointer-events-none text-slate-400">
                <Lock className="w-3.5 h-3.5" />
              </div>
              <input
                type={showConfirmPassword ? 'text' : 'password'}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="••••••••••••"
                className={`w-full pl-8 pr-8 py-1.5 text-xs rounded-lg bg-background border outline-none text-slate-900 dark:text-white transition-colors ${
                  confirmPassword.length > 0
                    ? passwordsMatch
                      ? 'border-emerald-500 focus:border-emerald-500'
                      : 'border-rose-500 focus:border-rose-500'
                    : 'border-border focus:border-primary-500'
                }`}
                required
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute inset-y-0 right-0 pr-2.5 flex items-center text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors"
                title={showConfirmPassword ? 'Ocultar confirmação' : 'Exibir confirmação'}
              >
                {showConfirmPassword ? (
                  <EyeOff className="w-3.5 h-3.5" />
                ) : (
                  <Eye className="w-3.5 h-3.5" />
                )}
              </button>
            </div>
            {confirmPassword.length > 0 && !passwordsMatch && (
              <p className="text-[10px] text-rose-500 font-medium">
                {t('security.passwordsDoNotMatch')}
              </p>
            )}
          </div>
        </div>

        {/* SRP & OCP Subcomponent: PasswordRequirementsChecklist */}
        <PasswordRequirementsChecklist
          requirements={requirements}
          allMet={validation.isValid && passwordsMatch}
        />

        {/* Submit Button */}
        <div className="flex justify-end pt-1">
          <button
            type="submit"
            disabled={!canSubmit}
            className="w-full sm:w-auto min-w-[200px] py-2 px-5 rounded-lg text-xs font-bold bg-primary-600 hover:bg-primary-500 text-white shadow-md shadow-primary-600/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <UserPlus className="w-3.5 h-3.5" />
            )}
            <span>{t('accounts.addUser')}</span>
          </button>
        </div>
      </form>
    </div>
  );
};
