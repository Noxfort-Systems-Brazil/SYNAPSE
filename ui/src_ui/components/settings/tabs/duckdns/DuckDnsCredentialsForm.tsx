// SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
// Copyright (C) 2026 Noxfort Systems
//
// File: ui/src_ui/components/settings/tabs/duckdns/DuckDnsCredentialsForm.tsx
// Description: Form fields for entering DuckDNS subdomain and auth token.

import React from 'react';
import { Eye, EyeOff, ExternalLink } from 'lucide-react';

interface DuckDnsCredentialsFormProps {
  domainInput: string;
  setDomainInput: (val: string) => void;
  tokenInput: string;
  setTokenInput: (val: string) => void;
  showToken: boolean;
  setShowToken: (val: boolean) => void;
}

export const DuckDnsCredentialsForm: React.FC<DuckDnsCredentialsFormProps> = ({
  domainInput,
  setDomainInput,
  tokenInput,
  setTokenInput,
  showToken,
  setShowToken,
}) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* Domain Field */}
      <div className="space-y-1.5">
        <label className="text-slate-700 dark:text-slate-300 font-semibold flex items-center justify-between">
          <span>Subdomínio DuckDNS:</span>
          <a
            href="https://www.duckdns.org"
            target="_blank"
            rel="noreferrer"
            className="text-[10px] text-primary-500 hover:underline flex items-center gap-0.5 font-normal"
          >
            Criar domínio gratuito <ExternalLink className="w-2.5 h-2.5" />
          </a>
        </label>
        <div className="flex items-center">
          <input
            type="text"
            placeholder="ex: prefeitura-transito"
            value={domainInput}
            onChange={(e) => setDomainInput(e.target.value)}
            className="flex-1 h-9 px-3 bg-surface dark:bg-background border border-border rounded-l-xl text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-primary-500 font-mono text-xs"
          />
          <span className="h-9 px-3 bg-slate-100 dark:bg-surfaceHover border border-l-0 border-border rounded-r-xl text-slate-500 dark:text-slate-400 font-mono text-xs flex items-center">
            .duckdns.org
          </span>
        </div>
      </div>

      {/* Token Field */}
      <div className="space-y-1.5">
        <label className="text-slate-700 dark:text-slate-300 font-semibold">
          Token da Conta DuckDNS:
        </label>
        <div className="relative">
          <input
            type={showToken ? 'text' : 'password'}
            placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
            value={tokenInput}
            onChange={(e) => setTokenInput(e.target.value)}
            className="w-full h-9 pl-3 pr-9 bg-surface dark:bg-background border border-border rounded-xl text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-primary-500 font-mono text-xs"
          />
          <button
            type="button"
            onClick={() => setShowToken(!showToken)}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
          >
            {showToken ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </div>
  );
};
