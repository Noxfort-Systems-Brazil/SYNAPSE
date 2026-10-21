// SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
// Copyright (C) 2026 Noxfort Systems
//
// File: ui/src_ui/components/sensors/edit/EditSensorForm.tsx
// Author: Gabriel Moraes
// Date: 2026-09-29

import React from 'react';
import { useTranslation } from 'react-i18next';
import {
  Crosshair,
  Radio,
  Globe,
  Loader2,
  Trash2,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import { MapEdgeData, MapNodeData } from '../../../types/topology';

export interface EditSensorFormProps {
  name: string;
  setName: (v: string) => void;
  isLocal: boolean;
  setIsLocal: (v: boolean) => void;
  sourceType: string;
  setSourceType: (v: string) => void;
  connectionString: string;
  setConnectionString: (v: string) => void;
  location: string;
  setLocation: (v: string) => void;
  isSaving: boolean;
  errorMsg: string | null;
  edges: MapEdgeData[];
  nodes: MapNodeData[];
  onPickOnMap: () => void;
  onSave: (e: React.FormEvent) => void;
  onCancel: () => void;
}

/**
 * Pure Presentational Form Component (SOLID: Single Responsibility & Humble View)
 * Displays input controls, validation feedback, and triggers callbacks.
 * Completely free of transport I/O, business validation, or state store coupling.
 */
export const EditSensorForm: React.FC<EditSensorFormProps> = ({
  name,
  setName,
  isLocal,
  setIsLocal,
  sourceType,
  setSourceType,
  connectionString,
  setConnectionString,
  location,
  setLocation,
  isSaving,
  errorMsg,
  edges,
  nodes,
  onPickOnMap,
  onSave,
  onCancel,
}) => {
  const { t } = useTranslation();

  return (
    <form onSubmit={onSave} className="space-y-4 text-xs">
      {errorMsg && (
        <div className="p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 rounded-xl text-rose-700 dark:text-rose-400 text-xs flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* 1. Nome */}
      <div className="space-y-1.5">
        <label className="text-slate-700 dark:text-slate-300 font-semibold">
          Nome de Identificação:
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Ex: Câmera Principal Norte"
          className="w-full h-10 px-3 bg-background border border-border rounded-xl text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-primary-500 font-sans text-xs transition-colors"
        />
      </div>

      {/* 2. Escopo: Local vs Global */}
      <div className="space-y-1.5">
        <label className="text-slate-700 dark:text-slate-300 font-semibold">
          Escopo / Origem:
        </label>
        <div className="grid grid-cols-2 gap-2">
          <button
            type="button"
            onClick={() => setIsLocal(true)}
            className={`py-2 px-3 rounded-xl border text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
              isLocal
                ? 'bg-accent-cyan/15 border-accent-cyan text-accent-cyan font-bold shadow-xs'
                : 'bg-background border-border text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Radio className="w-3.5 h-3.5" />
            <span>Sensor Local (IoT)</span>
          </button>
          <button
            type="button"
            onClick={() => setIsLocal(false)}
            className={`py-2 px-3 rounded-xl border text-xs font-semibold flex items-center justify-center gap-2 transition-all ${
              !isLocal
                ? 'bg-primary-500/15 border-primary-500 text-primary-600 dark:text-primary-400 font-bold shadow-xs'
                : 'bg-background border-border text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Globe className="w-3.5 h-3.5" />
            <span>Fonte Global (API)</span>
          </button>
        </div>
      </div>

      {/* 3. Via Viária / Elemento no Mapa */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <label className="text-slate-700 dark:text-slate-300 font-semibold">
            Via / Elemento Vinculado no Mapa:
          </label>
          {location ? (() => {
            const edge = edges.find(
              (e) => e.id === location || `-${e.id}` === location || e.id === location.replace(/^-/, '')
            );
            const node = !edge ? nodes.find((n) => n.id === location) : null;
            const displayName = edge?.name || node?.name || location;
            return (
              <span className="text-[10px] text-accent-cyan font-semibold flex items-center gap-1 font-mono" title={`ID: ${location}`}>
                <CheckCircle2 className="w-3 h-3 text-accent-cyan" />
                <span>{displayName}</span>
              </span>
            );
          })() : (
            <span className="text-[10px] text-slate-400 italic">
              Não vinculado
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <input
            type="text"
            list="edit-sensor-edges-list"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="Nome ou ID da Via/Cruzamento ou escolha no mapa..."
            className="flex-1 h-10 px-3 bg-background border border-border rounded-xl text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-primary-500 font-mono text-xs transition-colors"
          />
          <button
            type="button"
            onClick={onPickOnMap}
            disabled={edges.length === 0 && nodes.length === 0}
            className="h-10 px-3 bg-primary-600 hover:bg-primary-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 shadow-sm transition-all cursor-pointer whitespace-nowrap active:scale-95"
            title="Abrir mapa para clicar diretamente na via"
          >
            <Crosshair className="w-3.5 h-3.5 text-accent-cyan" />
            <span>No Mapa</span>
          </button>
          {location && (
            <button
              type="button"
              onClick={() => setLocation('')}
              className="h-10 px-2.5 bg-slate-100 dark:bg-slate-800 hover:bg-rose-100 dark:hover:bg-rose-950/40 text-slate-500 dark:text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 rounded-xl border border-border transition-colors cursor-pointer"
              title="Desvincular via"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Datalist autocomplete for edges & nodes */}
        <datalist id="edit-sensor-edges-list">
          {edges.map((e) => (
            <option key={e.id} value={e.id}>
              {e.name ? `${e.name} (${e.id})` : `Via ${e.id} (${e.from} → ${e.to})`}
            </option>
          ))}
          {nodes.map((n) => (
            <option key={n.id} value={n.id}>
              {n.name ? `${n.name} (${n.id})` : `Cruzamento ${n.id}`}
            </option>
          ))}
        </datalist>
      </div>

      {/* 4. Tipo de Fonte & Conexão */}
      <div className="grid grid-cols-3 gap-3">
        <div className="space-y-1.5 col-span-1">
          <label className="text-slate-700 dark:text-slate-300 font-semibold">
            Tipo:
          </label>
          <select
            value={sourceType}
            onChange={(e) => setSourceType(e.target.value)}
            className="w-full h-10 px-2.5 bg-background border border-border rounded-xl text-slate-900 dark:text-slate-100 focus:outline-none focus:border-primary-500 text-xs transition-colors"
          >
            <option value="HTTP">HTTP (REST)</option>
            <option value="MQTT Stream">MQTT Stream</option>
            <option value="REST API">API Externa</option>
            <option value="CSV">Arquivo CSV</option>
            <option value="SQL Database">Banco SQL</option>
          </select>
        </div>

        <div className="space-y-1.5 col-span-2">
          <label className="text-slate-700 dark:text-slate-300 font-semibold">
            Endpoint / String de Conexão:
          </label>
          <input
            type="text"
            value={connectionString}
            onChange={(e) => setConnectionString(e.target.value)}
            placeholder="Ex: http://192.168.1.50:8081/src_1"
            className="w-full h-10 px-3 bg-background border border-border rounded-xl text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-primary-500 font-mono text-xs transition-colors"
          />
        </div>
      </div>

      {/* Footer Actions */}
      <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-border/80">
        <button
          type="button"
          onClick={onCancel}
          disabled={isSaving}
          className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors"
        >
          {t('settings.cancel')}
        </button>
        <button
          type="submit"
          disabled={isSaving}
          className="px-5 py-2 bg-primary-600 hover:bg-primary-500 disabled:opacity-50 text-white rounded-xl text-xs font-bold flex items-center gap-2 shadow-sm transition-all cursor-pointer active:scale-95"
        >
          {isSaving && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
          <span>Salvar Alterações</span>
        </button>
      </div>
    </form>
  );
};
