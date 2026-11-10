// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { X, Globe, Database, Radio, Sliders, Landmark, UserCheck, History, Cloud } from 'lucide-react';
import { DatabaseSettingsTab } from './tabs/DatabaseSettingsTab';
import { MonitorSettingsTab } from './tabs/MonitorSettingsTab';
import { GeneralSettingsTab } from './tabs/GeneralSettingsTab';
import { MunicipalSettingsTab } from './tabs/MunicipalSettingsTab';
import { AccountSettingsTab } from './tabs/AccountSettingsTab';
import { AuditLogTab } from './tabs/AuditLogTab';
import { DuckDnsSettingsTab } from './tabs/DuckDnsSettingsTab';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<'municipal' | 'duckdns' | 'db' | 'monitor' | 'general' | 'accounts' | 'audit'>('municipal');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in select-none">
      <div className="w-full max-w-3xl glass-panel bg-surface p-6 rounded-2xl shadow-2xl border border-border space-y-6 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border/80 pb-4">
          <h2 className="text-base font-bold text-slate-900 dark:text-white tracking-tight flex items-center gap-2">
            <Sliders className="w-5 h-5 text-primary-500 dark:text-primary-400" />
            {t('settings.title')}
          </h2>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-surfaceHover transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-2 border-b border-border/80 pb-2 overflow-x-auto">
          <button
            onClick={() => setActiveTab('municipal')}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 shrink-0 ${
              activeTab === 'municipal'
                ? 'bg-primary-600 text-white shadow-md shadow-primary-600/20'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-surfaceHover'
            }`}
          >
            <Landmark className="w-4 h-4" />
            <span>{t('settings.tabs.municipal')}</span>
          </button>

          <button
            onClick={() => setActiveTab('db')}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 shrink-0 ${
              activeTab === 'db'
                ? 'bg-primary-600 text-white shadow-md shadow-primary-600/20'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-surfaceHover'
            }`}
          >
            <Database className="w-4 h-4" />
            <span>{t('settings.tabs.db')}</span>
          </button>

          <button
            onClick={() => setActiveTab('duckdns')}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 shrink-0 ${
              activeTab === 'duckdns'
                ? 'bg-primary-600 text-white shadow-md shadow-primary-600/20'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-surfaceHover'
            }`}
          >
            <Cloud className="w-4 h-4" />
            <span>{t('settings.tabs.duckdns')}</span>
          </button>

          <button
            onClick={() => setActiveTab('monitor')}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 shrink-0 ${
              activeTab === 'monitor'
                ? 'bg-primary-600 text-white shadow-md shadow-primary-600/20'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-surfaceHover'
            }`}
          >
            <Radio className="w-4 h-4" />
            <span>{t('settings.tabs.monitor')}</span>
          </button>

          <button
            onClick={() => setActiveTab('general')}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 shrink-0 ${
              activeTab === 'general'
                ? 'bg-primary-600 text-white shadow-md shadow-primary-600/20'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-surfaceHover'
            }`}
          >
            <Globe className="w-4 h-4" />
            <span>{t('settings.tabs.general')}</span>
          </button>

          <button
            onClick={() => setActiveTab('accounts')}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 shrink-0 ${
              activeTab === 'accounts'
                ? 'bg-primary-600 text-white shadow-md shadow-primary-600/20'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-surfaceHover'
            }`}
          >
            <UserCheck className="w-4 h-4" />
            <span>{t('settings.tabs.accounts')}</span>
          </button>

          <button
            onClick={() => setActiveTab('audit')}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 shrink-0 ${
              activeTab === 'audit'
                ? 'bg-primary-600 text-white shadow-md shadow-primary-600/20'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-surfaceHover'
            }`}
          >
            <History className="w-4 h-4" />
            <span>{t('settings.tabs.audit')}</span>
          </button>
        </div>

        {/* Tab Content */}
        <div className="min-h-[280px]">
          {activeTab === 'municipal' && <MunicipalSettingsTab />}
          {activeTab === 'db' && <DatabaseSettingsTab />}
          {activeTab === 'duckdns' && <DuckDnsSettingsTab />}
          {activeTab === 'monitor' && <MonitorSettingsTab />}
          {activeTab === 'general' && <GeneralSettingsTab />}
          {activeTab === 'accounts' && <AccountSettingsTab />}
          {activeTab === 'audit' && <AuditLogTab />}
        </div>
      </div>
    </div>
  );
};
