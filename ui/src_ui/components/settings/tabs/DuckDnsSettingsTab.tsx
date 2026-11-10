// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { Loader2, Activity, Check, AlertCircle } from 'lucide-react';
import { useDuckDnsSettings } from './duckdns/useDuckDnsSettings';
import { DuckDnsHeaderCard } from './duckdns/DuckDnsHeaderCard';
import { DuckDnsCredentialsForm } from './duckdns/DuckDnsCredentialsForm';
import { DuckDnsCaddyCard } from './duckdns/DuckDnsCaddyCard';
import { DuckDnsPreviewCard } from './duckdns/DuckDnsPreviewCard';

export const DuckDnsSettingsTab: React.FC = () => {
  const {
    config,
    domainInput,
    setDomainInput,
    tokenInput,
    setTokenInput,
    showToken,
    setShowToken,
    caddyEnabled,
    setCaddyEnabled,
    loading,
    testing,
    saving,
    copied,
    feedback,
    cleanDomain,
    previewUrl,
    handleCopy,
    handleTest,
    handleSaveAndApply,
    isOnline,
  } = useDuckDnsSettings();

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-slate-500">
        <Loader2 className="w-6 h-6 animate-spin text-primary-500 mb-2" />
        <span className="text-xs">Carregando configurações de rede...</span>
      </div>
    );
  }

  const hasValidInputs = Boolean(cleanDomain(domainInput) && tokenInput.trim());

  return (
    <div className="space-y-4 text-xs">
      <DuckDnsHeaderCard
        isOnline={isOnline}
        enabled={config.enabled}
        saving={saving}
        canConnect={hasValidInputs}
        onToggle={() => handleSaveAndApply(!config.enabled)}
      />

      <DuckDnsCredentialsForm
        domainInput={domainInput}
        setDomainInput={setDomainInput}
        tokenInput={tokenInput}
        setTokenInput={setTokenInput}
        showToken={showToken}
        setShowToken={setShowToken}
      />

      <DuckDnsCaddyCard
        caddyEnabled={caddyEnabled}
        setCaddyEnabled={setCaddyEnabled}
      />

      <DuckDnsPreviewCard
        previewUrl={previewUrl}
        copied={copied}
        onCopy={handleCopy}
      />

      {feedback && (
        <div
          className={`p-3 rounded-xl border flex items-center gap-2 text-[11px] ${
            feedback.ok
              ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-600 dark:text-emerald-400'
              : 'bg-rose-500/10 border-rose-500/30 text-rose-600 dark:text-rose-400'
          }`}
        >
          {feedback.ok ? (
            <Check className="w-4 h-4 shrink-0" />
          ) : (
            <AlertCircle className="w-4 h-4 shrink-0" />
          )}
          <span>{feedback.msg}</span>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center justify-between pt-2 border-t border-border/80">
        <button
          type="button"
          onClick={handleTest}
          disabled={testing || !hasValidInputs}
          className="px-3.5 py-2 bg-surface dark:bg-background border border-border hover:border-slate-400 dark:hover:border-slate-600 rounded-xl text-slate-700 dark:text-slate-300 font-semibold flex items-center gap-1.5 transition-all cursor-pointer active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {testing ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Activity className="w-3.5 h-3.5 text-primary-500" />
          )}
          <span>Testar Conexão</span>
        </button>

        <button
          type="button"
          onClick={() => handleSaveAndApply(true)}
          disabled={saving || !hasValidInputs}
          className="px-4 py-2 bg-primary-600 hover:bg-primary-500 text-white rounded-xl font-bold flex items-center gap-1.5 shadow-md shadow-primary-600/20 transition-all cursor-pointer active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {saving ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Check className="w-3.5 h-3.5" />
          )}
          <span>Salvar Configurações</span>
        </button>
      </div>
    </div>
  );
};
