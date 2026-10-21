// SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
// Copyright (C) 2026 Noxfort Systems
//
// File: ui/src_ui/components/wizard/add_source/SourceTypeSelector.tsx
// Author: Gabriel Moraes
// Date: 2026-09-14

import React from 'react';
import { Cloud, Radio, Layers, Lock, AlertTriangle } from 'lucide-react';

interface SourceTypeSelectorProps {
  onSelectType: (type: 'LOCAL' | 'GLOBAL') => void;
  onOpenBatchModal: () => void;
  isDuckDnsActive?: boolean;
}

export const SourceTypeSelector: React.FC<SourceTypeSelectorProps> = ({
  onSelectType,
  onOpenBatchModal,
  isDuckDnsActive = true,
}) => {
  return (
    <div className="space-y-4 text-xs">
      {!isDuckDnsActive && (
        <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl flex items-start gap-2.5 text-[11px] text-amber-700 dark:text-amber-400">
          <AlertTriangle className="w-4 h-4 shrink-0 text-amber-500 mt-0.5" />
          <div className="space-y-0.5">
            <span className="font-bold block">Acesso Remoto (DuckDNS) Não Configurado</span>
            <p className="text-[10px] text-slate-500 dark:text-slate-400 leading-relaxed">
              Para cadastrar e conectar sensores locais (câmeras de trânsito, radares ou simuladores locais), é obrigatório configurar e ativar o DuckDNS em <strong>Configurações &gt; Acesso Remoto</strong>.
            </p>
          </div>
        </div>
      )}

      <p className="text-slate-700 dark:text-slate-300 font-semibold">
        Selecione a tipologia de origem do dado:
      </p>

      <div className="grid grid-cols-2 gap-4">
        {/* Option Local */}
        <div
          onClick={() => {
            if (isDuckDnsActive) {
              onSelectType('LOCAL');
            }
          }}
          className={`p-5 rounded-2xl bg-surface dark:bg-background/80 border transition-all flex flex-col items-center text-center space-y-3 shadow-xs relative ${
            isDuckDnsActive
              ? 'border-border hover:border-accent-cyan/60 cursor-pointer group'
              : 'border-amber-500/30 opacity-60 cursor-not-allowed bg-slate-100/50 dark:bg-surface/30'
          }`}
          title={
            isDuckDnsActive
              ? 'Adicionar câmera local ou radar'
              : 'DuckDNS inativo: configure o DuckDNS em Configurações para habilitar sensores locais'
          }
        >
          {!isDuckDnsActive && (
            <div className="absolute top-3 right-3 flex items-center gap-1 px-1.5 py-0.5 rounded-md bg-amber-500/15 border border-amber-500/30 text-amber-500 text-[10px] font-bold">
              <Lock className="w-3 h-3" />
              <span>Bloqueado</span>
            </div>
          )}
          <div
            className={`w-12 h-12 rounded-xl flex items-center justify-center transition-transform ${
              isDuckDnsActive
                ? 'bg-accent-cyan/10 border border-accent-cyan/30 text-accent-cyan group-hover:scale-110'
                : 'bg-slate-500/10 border border-slate-500/20 text-slate-400'
            }`}
          >
            <Radio className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center justify-center gap-1.5">
              <span>Dispositivo Local (Push)</span>
            </h3>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
              {isDuckDnsActive
                ? 'Câmeras, laços indutivos ou radares conectados via rede local ou 4G.'
                : 'Exige DuckDNS ativo para fornecer URL oficial e segura de ingestão.'}
            </p>
          </div>
        </div>

        {/* Option Global */}
        <div
          onClick={() => onSelectType('GLOBAL')}
          className="p-5 rounded-2xl bg-surface dark:bg-background/80 border border-border hover:border-primary-500/60 cursor-pointer transition-all flex flex-col items-center text-center space-y-3 group shadow-xs"
        >
          <div className="w-12 h-12 rounded-xl bg-primary-500/10 border border-primary-500/30 flex items-center justify-center text-primary-500 dark:text-primary-400 group-hover:scale-110 transition-transform">
            <Cloud className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">API Global (Pull)</h3>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
              Serviços em nuvem, feeds externos de trânsito (Waze, TomTom).
            </p>
          </div>
        </div>
      </div>

      {/* Batch Import Option */}
      <div
        onClick={() => {
          if (isDuckDnsActive) {
            onOpenBatchModal();
          }
        }}
        className={`p-4 rounded-2xl border transition-all flex items-center justify-between shadow-xs ${
          isDuckDnsActive
            ? 'bg-primary-500/5 border-primary-500/30 hover:border-primary-500/60 cursor-pointer group'
            : 'bg-slate-100/50 dark:bg-surface/30 border-border opacity-60 cursor-not-allowed'
        }`}
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary-500/10 border border-primary-500/30 flex items-center justify-center text-primary-500 group-hover:scale-105 transition-transform">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-slate-900 dark:text-white">
              Importação em Lote via CSV (name,location)
            </h3>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
              {isDuckDnsActive
                ? 'Cadastre dezenas ou centenas de câmeras/laços de uma só vez e exporte os perfis.'
                : 'Importação em lote de sensores locais bloqueada: ative o DuckDNS primeiro.'}
            </p>
          </div>
        </div>
        {isDuckDnsActive ? (
          <span className="text-xs font-semibold text-primary-500 group-hover:translate-x-0.5 transition-transform">
            Abrir &rarr;
          </span>
        ) : (
          <span className="text-[10px] font-bold text-amber-500 flex items-center gap-1">
            <Lock className="w-3 h-3" /> Requer DuckDNS
          </span>
        )}
      </div>
    </div>
  );
};
