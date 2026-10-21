// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Globe, 
  Settings as SettingsIcon, 
  Terminal, 
  Sun, 
  Moon 
} from 'lucide-react';
import { useSystemStore, useSecurityStore } from '../../../stores';

export interface HeaderQuickActionsProps {
  openSettings: () => void;
  openLogs: () => void;
  isLogsOpen: boolean;
  children?: React.ReactNode;
}

/**
 * Atomic subcomponent for system utilities (Theme, Language, Logs and Protected Settings) (SRP + OCP by Composition).
 */
const SUPPORTED_LANGUAGES = [
  { code: 'pt_BR', label: 'PT-BR', prefix: 'pt' },
  { code: 'en_US', label: 'EN-US', prefix: 'en' },
  { code: 'es_ES', label: 'ES-ES', prefix: 'es' },
  { code: 'fr_FR', label: 'FR-FR', prefix: 'fr' },
  { code: 'ru_RU', label: 'RU-RU', prefix: 'ru' },
  { code: 'zh_CN', label: 'ZH-CN', prefix: 'zh' },
];

export const HeaderQuickActions: React.FC<HeaderQuickActionsProps> = ({
  openSettings,
  openLogs,
  isLogsOpen,
  children,
}) => {
  const { t, i18n } = useTranslation();
  const { theme, toggleTheme } = useSystemStore();
  const { requestAuth } = useSecurityStore();

  const cycleLanguage = () => {
    const currentCode = (i18n.language || 'pt_BR').replace('-', '_');
    const currentIndex = SUPPORTED_LANGUAGES.findIndex(
      (l) => l.code === currentCode || currentCode.startsWith(l.prefix)
    );
    const nextIndex = (currentIndex + 1) % SUPPORTED_LANGUAGES.length;
    i18n.changeLanguage(SUPPORTED_LANGUAGES[nextIndex].code);
  };

  const currentLang = SUPPORTED_LANGUAGES.find(
    (l) => l.code === (i18n.language || 'pt_BR').replace('-', '_') || (i18n.language || '').startsWith(l.prefix)
  ) || SUPPORTED_LANGUAGES[0];

  return (
    <>
      {/* Alternador de Tema (Light / Dark) */}
      <button
        onClick={toggleTheme}
        title={theme === 'dark' ? 'Mudar para Modo Claro' : 'Mudar para Modo Escuro'}
        className="p-2 rounded-lg bg-surface border border-border text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:border-primary-500/50 transition-all flex items-center justify-center shadow-sm shrink-0"
      >
        {theme === 'dark' ? (
          <Sun className="w-4 h-4 text-accent-amber animate-spin-slow" />
        ) : (
          <Moon className="w-4 h-4 text-primary-600" />
        )}
      </button>

      {/* Alternador de Idioma */}
      <button
        onClick={cycleLanguage}
        title={t('settings.language')}
        className="flex items-center gap-1.5 px-2.5 sm:px-3 py-1.5 text-xs font-semibold bg-surface border border-border rounded-lg text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:border-primary-500/50 transition-all shadow-sm shrink-0 whitespace-nowrap active:scale-95"
      >
        <Globe className="w-3.5 h-3.5 text-accent-cyan shrink-0" />
        <span className="whitespace-nowrap">{currentLang.label}</span>
      </button>

      {/* Botão para Drawer de Logs */}
      <button
        onClick={openLogs}
        title={t('nav.logs')}
        className={`p-2 rounded-lg border transition-all shrink-0 ${
          isLogsOpen
            ? 'bg-primary-600/15 border-primary-500/50 text-primary-600 dark:text-primary-400'
            : 'bg-surface border-border text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:border-slate-400 dark:hover:border-slate-600'
        }`}
      >
        <Terminal className="w-4 h-4" />
      </button>

      {/* Slot composicional (ex: HeaderUserBadge) */}
      {children}

      {/* Botão de Configurações protegido por autenticação */}
      <button
        onClick={() => requestAuth(() => openSettings())}
        title={t('nav.settings')}
        className="p-2 rounded-lg bg-surface border border-border text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:border-slate-400 dark:hover:border-slate-600 transition-all shrink-0"
      >
        <SettingsIcon className="w-4 h-4" />
      </button>
    </>
  );
};
