// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Globe, Sun, Moon, Palette, Trash2, RotateCcw } from 'lucide-react';
import { useSystemStore, useTopologyStore, useSensorsStore, useEtlStore } from '../../../stores';
import { systemService } from '../../../services/api';

export const GeneralSettingsTab: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { theme, setTheme } = useSystemStore();
  const [isResetting, setIsResetting] = useState(false);
  const [resetNotice, setResetNotice] = useState<string | null>(null);
  const [logLevel, setLogLevel] = useState(() => {
    try {
      return localStorage.getItem('synapse_log_level') || 'INFO';
    } catch {
      return 'INFO';
    }
  });

  const handleLogLevelChange = (newLevel: string) => {
    setLogLevel(newLevel);
    try {
      localStorage.setItem('synapse_log_level', newLevel);
    } catch {}
  };

  const handleResetWorkspace = async () => {
    if (!window.confirm('Tem certeza que deseja limpar todas as fontes de dados e o mapa para testar do zero?')) {
      return;
    }
    setIsResetting(true);
    setResetNotice(null);
    try {
      await systemService.resetWorkspace();
      useTopologyStore.getState().clearTopology();
      useSensorsStore.getState().setSources([]);
      useSensorsStore.getState().setSelectedSourceId(null);
      useEtlStore.getState().resetEtlState();
      setResetNotice('✅ Espaço de trabalho zerado com sucesso! A interface agora está vazia.');
      setTimeout(() => setResetNotice(null), 6000);
    } catch (err: any) {
      setResetNotice(`❌ Erro ao resetar: ${err?.message || err}`);
    } finally {
      setIsResetting(false);
    }
  };

  return (
    <div className="space-y-5 text-xs">
      {/* Theme Mode Selector */}
      <div className="space-y-2">
        <label className="text-slate-700 dark:text-slate-300 font-semibold flex items-center gap-1.5">
          <Palette className="w-3.5 h-3.5 text-primary-500" />
          <span>Tema Visual da Interface</span>
        </label>
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => setTheme('dark')}
            className={`py-2.5 px-3 rounded-xl border text-xs font-bold transition-all flex items-center justify-center gap-2 ${
              theme === 'dark'
                ? 'bg-primary-600/20 border-primary-500 text-primary-400 dark:text-primary-300 shadow-sm'
                : 'bg-surface border-border text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Moon className="w-4 h-4 text-primary-400" />
            <span>Modo Escuro (Obsidian Slate)</span>
          </button>
          <button
            onClick={() => setTheme('light')}
            className={`py-2.5 px-3 rounded-xl border text-xs font-bold transition-all flex items-center justify-center gap-2 ${
              theme === 'light'
                ? 'bg-primary-600/20 border-primary-500 text-primary-600 dark:text-primary-300 shadow-sm'
                : 'bg-surface border-border text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Sun className="w-4 h-4 text-accent-amber" />
            <span>Modo Claro (Polar Slate)</span>
          </button>
        </div>
      </div>

      {/* Language Selector */}
      <div className="space-y-2">
        <label className="text-slate-700 dark:text-slate-300 font-semibold flex items-center gap-1.5">
          <Globe className="w-3.5 h-3.5 text-accent-cyan" />
          {t('settings.language')}
        </label>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          <button
            onClick={() => i18n.changeLanguage('pt_BR')}
            className={`py-2.5 px-3 rounded-xl border text-xs font-bold transition-all ${
              i18n.language.startsWith('pt')
                ? 'bg-primary-600/20 border-primary-500 text-primary-600 dark:text-primary-300'
                : 'bg-surface border-border text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            🇧🇷 Português (Brasil)
          </button>
          <button
            onClick={() => i18n.changeLanguage('en_US')}
            className={`py-2.5 px-3 rounded-xl border text-xs font-bold transition-all ${
              i18n.language.startsWith('en')
                ? 'bg-primary-600/20 border-primary-500 text-primary-600 dark:text-primary-300'
                : 'bg-surface border-border text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            🇺🇸 English (US)
          </button>
          <button
            onClick={() => i18n.changeLanguage('es_ES')}
            className={`py-2.5 px-3 rounded-xl border text-xs font-bold transition-all ${
              i18n.language.startsWith('es')
                ? 'bg-primary-600/20 border-primary-500 text-primary-600 dark:text-primary-300'
                : 'bg-surface border-border text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            🇪🇸 Español
          </button>
          <button
            onClick={() => i18n.changeLanguage('fr_FR')}
            className={`py-2.5 px-3 rounded-xl border text-xs font-bold transition-all ${
              i18n.language.startsWith('fr')
                ? 'bg-primary-600/20 border-primary-500 text-primary-600 dark:text-primary-300'
                : 'bg-surface border-border text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            🇫🇷 Français
          </button>
          <button
            onClick={() => i18n.changeLanguage('ru_RU')}
            className={`py-2.5 px-3 rounded-xl border text-xs font-bold transition-all ${
              i18n.language.startsWith('ru')
                ? 'bg-primary-600/20 border-primary-500 text-primary-600 dark:text-primary-300'
                : 'bg-surface border-border text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            🇷🇺 Русский
          </button>
          <button
            onClick={() => i18n.changeLanguage('zh_CN')}
            className={`py-2.5 px-3 rounded-xl border text-xs font-bold transition-all ${
              i18n.language.startsWith('zh')
                ? 'bg-primary-600/20 border-primary-500 text-primary-600 dark:text-primary-300'
                : 'bg-surface border-border text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            🇨🇳 简体中文
          </button>
        </div>
      </div>

      {/* Log Level */}
      <div className="space-y-1 pt-1">
        <label className="text-slate-700 dark:text-slate-300 font-semibold">Nível de Registro de Logs:</label>
        <select
          value={logLevel}
          onChange={(e) => handleLogLevelChange(e.target.value)}
          className="w-full h-9 px-3 bg-background border border-border rounded-xl text-slate-800 dark:text-slate-200 font-mono"
        >
          <option value="DEBUG">DEBUG (Detalhado)</option>
          <option value="INFO">INFO (Padrão Operacional)</option>
          <option value="WARNING">WARNING (Avisos)</option>
          <option value="ERROR">ERROR (Erros Críticos)</option>
        </select>
      </div>

      {/* Workspace Maintenance / Reset */}
      <div className="pt-4 border-t border-border space-y-3">
        <div>
          <label className="text-rose-600 dark:text-rose-400 font-bold flex items-center gap-1.5">
            <Trash2 className="w-3.5 h-3.5" />
            <span>Zona de Manutenção: Reset do Espaço de Trabalho</span>
          </label>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
            Limpa todas as fontes de dados, rede viária/mapa em memória e no disco, e esvazia o vault de arquivos para testar o sistema do zero.
          </p>
        </div>

        <button
          onClick={handleResetWorkspace}
          disabled={isResetting}
          className="w-full py-2.5 px-4 rounded-xl bg-rose-600/10 hover:bg-rose-600/20 text-rose-600 dark:text-rose-400 border border-rose-500/30 font-bold text-xs flex items-center justify-center gap-2 transition-all disabled:opacity-50"
        >
          <RotateCcw className={`w-3.5 h-3.5 ${isResetting ? 'animate-spin' : ''}`} />
          <span>{isResetting ? 'Resetando Espaço de Trabalho...' : 'Limpar Fontes e Resetar Espaço (Testar do Zero)'}</span>
        </button>

        {resetNotice && (
          <div className="p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 text-xs font-medium">
            {resetNotice}
          </div>
        )}
      </div>
    </div>
  );
};

