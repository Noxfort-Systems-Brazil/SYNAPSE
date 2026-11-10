// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { Check, Copy, MapPin, ShieldCheck } from 'lucide-react';
import { useTopologyStore } from '../../../stores';

interface SourceConfigFormProps {
  sourceType: 'LOCAL' | 'GLOBAL';
  sourceName: string;
  setSourceName: (v: string) => void;
  selectedLocation: string;
  setSelectedLocation: (v: string) => void;
  globalUrl: string;
  setGlobalUrl: (v: string) => void;
  localIp: string;
  gatewayPort: number;
  sourceId: string;
  copiedField: string | null;
  onCopy: (text: string, field: string) => void;
  ingressUrl?: string;
}

export const SourceConfigForm: React.FC<SourceConfigFormProps> = ({
  sourceType,
  sourceName,
  setSourceName,
  selectedLocation,
  setSelectedLocation,
  globalUrl,
  setGlobalUrl,
  localIp,
  gatewayPort,
  sourceId,
  copiedField,
  onCopy,
  ingressUrl,
}) => {
  const edges = useTopologyStore((s) => s.edges);
  const nodes = useTopologyStore((s) => s.nodes);
  const startPickingElement = useTopologyStore((s) => s.startPickingElement);
  const effectiveUrl = ingressUrl || `http://${localIp}:${gatewayPort}/${sourceId}`;
  const isHttps = effectiveUrl.startsWith('https://');

  return (
    <div className="space-y-4 text-xs">
      <div className="space-y-1.5">
        <label className="text-slate-700 dark:text-slate-300 font-semibold">
          1. Nome de Identificação da Fonte:
        </label>
        <input
          type="text"
          placeholder="Ex: Câmera Av. Paulista Norte"
          value={sourceName}
          onChange={(e) => setSourceName(e.target.value)}
          className="w-full h-10 px-3 bg-surface dark:bg-background border border-border rounded-xl text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-primary-500 font-sans text-xs"
        />
      </div>

      {sourceType === 'LOCAL' && (
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <label className="text-slate-700 dark:text-slate-300 font-semibold">
              2. Rua / Via Monitorada (Localização):
            </label>
            {selectedLocation && (() => {
              const edge = edges.find(
                (e) => e.id === selectedLocation || `-${e.id}` === selectedLocation || e.id === selectedLocation.replace(/^-/, '')
              );
              const node = !edge ? nodes.find((n) => n.id === selectedLocation) : null;
              const displayName = edge?.name || node?.name || selectedLocation;
              return (
                <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold flex items-center gap-1 font-mono" title={`ID: ${selectedLocation}`}>
                  <Check className="w-3 h-3 text-emerald-500" />
                  <span>Via: {displayName}</span>
                </span>
              );
            })()}
          </div>

          <div className="flex items-center gap-2">
            <input
              type="text"
              list="add-source-edges-list"
              placeholder="Selecione na lista ou clique em Escolher no Mapa..."
              value={selectedLocation}
              onChange={(e) => setSelectedLocation(e.target.value)}
              className="flex-1 h-10 px-3 bg-surface dark:bg-background border border-border rounded-xl text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-primary-500 font-mono text-xs"
            />
            <button
              type="button"
              onClick={() => {
                startPickingElement({
                  prompt: `Clique na via ou cruzamento no mapa para vincular ao sensor "${
                    sourceName.trim() || sourceId
                  }".`,
                  onPicked: (elementId) => {
                    setSelectedLocation(elementId);
                  },
                });
              }}
              disabled={edges.length === 0 && nodes.length === 0}
              className="h-10 px-3 bg-primary-600 hover:bg-primary-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 shadow-sm transition-all cursor-pointer whitespace-nowrap active:scale-95"
              title={
                edges.length === 0 && nodes.length === 0
                  ? 'Nenhum mapa carregado no momento'
                  : 'Escolher a via clicando diretamente no mapa interativo'
              }
            >
              <MapPin className="w-4 h-4 text-accent-cyan" />
              <span>Escolher no Mapa</span>
            </button>
          </div>

          <datalist id="add-source-edges-list">
            {edges.map((edge) => (
              <option key={`edge-${edge.id}`} value={edge.id}>
                {edge.name ? `${edge.name} (${edge.id})` : `${edge.id} (Via: ${edge.from} → ${edge.to})`}
              </option>
            ))}
            {nodes.map((node) => (
              <option key={`node-${node.id}`} value={node.id}>
                {node.name ? `${node.name} (${node.id})` : `${node.id} (Cruzamento ${node.is_tls ? 'com Semáforo' : 'Geral'})`}
              </option>
            ))}
          </datalist>
          <p className="text-[10px] text-slate-500 dark:text-slate-400">
            {edges.length > 0
              ? `Você pode digitar o ID, escolher da lista acima ou clicar em "Escolher no Mapa" para selecionar a via visualmente. (${edges.length} vias carregadas)`
              : 'A via monitorada por este sensor receberá destaque exclusivo no mapa.'}
          </p>
        </div>
      )}

      {sourceType === 'GLOBAL' ? (
        <div className="space-y-1.5">
          <label className="text-slate-700 dark:text-slate-300 font-semibold">
            2. Endpoint URL (REST / Stream):
          </label>
          <input
            type="text"
            placeholder="https://api.provedor.com/v1/traffic"
            value={globalUrl}
            onChange={(e) => setGlobalUrl(e.target.value)}
            className="w-full h-10 px-3 bg-surface dark:bg-background border border-border rounded-xl text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-primary-500 font-mono text-xs"
          />
        </div>
      ) : (
        <div className="space-y-3 p-4 bg-slate-50 dark:bg-background/80 border border-border rounded-xl">
          <span className="font-bold text-slate-900 dark:text-white block">
            Instruções para Configuração do Sensor:
          </span>

          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-slate-500 dark:text-slate-400 text-[11px] font-semibold">
                URL de Envio (POST):
              </span>
              {isHttps && (
                <span className="text-[10px] text-emerald-500 font-semibold flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3" /> DuckDNS HTTPS
                </span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <input
                type="text"
                readOnly
                value={effectiveUrl}
                className="w-full h-8 px-2.5 bg-surface dark:bg-background border border-border rounded-lg text-accent-cyan font-mono text-xs font-semibold"
              />
              <button
                type="button"
                onClick={() => onCopy(effectiveUrl, 'url')}
                className="px-2.5 h-8 bg-surface dark:bg-background border border-border hover:border-slate-400 dark:hover:border-slate-600 rounded-lg text-slate-700 dark:text-slate-300 flex items-center gap-1 font-semibold"
              >
                {copiedField === 'url' ? (
                  <Check className="w-3.5 h-3.5 text-emerald-500 dark:text-emerald-400" />
                ) : (
                  <Copy className="w-3.5 h-3.5" />
                )}
              </button>
            </div>
          </div>

          <div className="space-y-1">
            <span className="text-slate-500 dark:text-slate-400 text-[11px] font-semibold">
              ID do Sensor (deve constar no JSON):
            </span>
            <div className="flex items-center gap-2">
              <input
                type="text"
                readOnly
                value={sourceId}
                className="w-full h-8 px-2.5 bg-surface dark:bg-background border border-border rounded-lg text-accent-cyan font-mono text-xs font-bold"
              />
              <button
                onClick={() => onCopy(sourceId, 'id')}
                className="px-2.5 h-8 bg-surface dark:bg-background border border-border hover:border-slate-400 dark:hover:border-slate-600 rounded-lg text-slate-700 dark:text-slate-300 flex items-center gap-1 font-semibold"
              >
                {copiedField === 'id' ? (
                  <Check className="w-3.5 h-3.5 text-emerald-500 dark:text-emerald-400" />
                ) : (
                  <Copy className="w-3.5 h-3.5" />
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
