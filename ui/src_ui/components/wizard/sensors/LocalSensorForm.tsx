// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { Copy, Check, MapPin, ShieldCheck, Lock, AlertTriangle } from 'lucide-react';
import { MapEdgeData, MapNodeData } from '../../../types/topology';

export interface LocalSensorFormProps {
  selectedLocation: string;
  onChangeLocation: (location: string) => void;
  edges: MapEdgeData[];
  nodes: MapNodeData[];
  localIp: string;
  gatewayPort: number;
  sensorId: string;
  copiedField: string | null;
  onCopy: (text: string, field: string) => void;
  onPickOnMap?: () => void;
  ingressUrl?: string;
  isDuckDnsActive?: boolean;
}

export const LocalSensorForm: React.FC<LocalSensorFormProps> = ({
  selectedLocation,
  onChangeLocation,
  edges,
  nodes,
  localIp,
  gatewayPort,
  sensorId,
  copiedField,
  onCopy,
  onPickOnMap,
  ingressUrl,
  isDuckDnsActive = true,
}) => {
  const endpointUrl = `http://${localIp}:${gatewayPort}/${sensorId}`;
  const effectiveUrl = ingressUrl || endpointUrl;
  const isHttps = effectiveUrl.startsWith('https://');

  return (
    <div className="space-y-4">
      {!isDuckDnsActive && (
        <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl flex items-start gap-2 text-[11px] text-amber-700 dark:text-amber-400">
          <AlertTriangle className="w-4 h-4 shrink-0 text-amber-500 mt-0.5" />
          <div className="space-y-0.5">
            <span className="font-bold block">DuckDNS Obrigatório</span>
            <p className="text-[10px] text-slate-500 dark:text-slate-400">
              Não é possível conectar sensores locais sem o DuckDNS configurado e ativo. Acesse Configurações &gt; Acesso Remoto.
            </p>
          </div>
        </div>
      )}

      {/* Street / Location Selection */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <label className="text-slate-700 dark:text-slate-300 font-semibold text-xs">
            Rua / Via Monitorada (Localização):
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
            list="sensors-step-edges-list"
            placeholder="Selecione na lista ou clique em Escolher no Mapa..."
            value={selectedLocation}
            onChange={(e) => onChangeLocation(e.target.value)}
            className="flex-1 h-9 px-3 bg-surface dark:bg-background border border-border rounded-xl text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-emerald-500 font-mono text-xs"
          />
          {onPickOnMap && (
            <button
              type="button"
              onClick={onPickOnMap}
              disabled={edges.length === 0 && nodes.length === 0}
              className="h-9 px-3 bg-primary-600 hover:bg-primary-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 shadow-sm transition-all cursor-pointer whitespace-nowrap active:scale-95"
              title={
                edges.length === 0 && nodes.length === 0
                  ? 'Nenhum mapa carregado no momento'
                  : 'Escolher a via clicando diretamente no mapa interativo'
              }
            >
              <MapPin className="w-3.5 h-3.5 text-accent-cyan" />
              <span>Escolher no Mapa</span>
            </button>
          )}
        </div>

        <datalist id="sensors-step-edges-list">
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
            : 'A rua onde o sensor local for vinculado receberá renderização destacada no mapa.'}
        </p>
      </div>

      {/* Endpoint and Sensor ID Copy Box */}
      <div className="space-y-2 p-3 bg-slate-50 dark:bg-surface/80 border border-border rounded-xl">
        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-slate-500 dark:text-slate-400 text-[10px] font-semibold">
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
              className="w-full h-7 px-2 bg-surface dark:bg-background border border-border rounded-lg text-accent-cyan font-mono text-xs font-semibold"
            />
            <button
              type="button"
              onClick={() => onCopy(effectiveUrl, 'url')}
              className="px-2 h-7 bg-surface dark:bg-background border border-border hover:border-slate-400 dark:hover:border-slate-500 rounded-lg text-slate-700 dark:text-slate-300 flex items-center gap-1 cursor-pointer"
              title="Copiar URL"
            >
              {copiedField === 'url' ? (
                <Check className="w-3 h-3 text-emerald-500 dark:text-emerald-400" />
              ) : (
                <Copy className="w-3 h-3" />
              )}
            </button>
          </div>
        </div>

        <div className="space-y-1">
          <span className="text-slate-500 dark:text-slate-400 text-[10px] font-semibold">
            ID do Sensor (payload JSON):
          </span>
          <div className="flex items-center gap-2">
            <input
              type="text"
              readOnly
              value={sensorId}
              className="w-full h-7 px-2 bg-surface dark:bg-background border border-border rounded-lg text-accent-cyan font-mono text-xs font-bold"
            />
            <button
              type="button"
              onClick={() => onCopy(sensorId, 'id')}
              className="px-2 h-7 bg-surface dark:bg-background border border-border hover:border-slate-400 dark:hover:border-slate-500 rounded-lg text-slate-700 dark:text-slate-300 flex items-center gap-1 cursor-pointer"
              title="Copiar ID"
            >
              {copiedField === 'id' ? (
                <Check className="w-3 h-3 text-emerald-500 dark:text-emerald-400" />
              ) : (
                <Copy className="w-3 h-3" />
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
