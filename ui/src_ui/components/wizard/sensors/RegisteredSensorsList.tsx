// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { useTranslation } from 'react-i18next';
import { Radio, Trash2, Pencil } from 'lucide-react';
import { DataSourceItem } from '../../../types/sensors';
import { useTopologyStore } from '../../../stores';

export interface RegisteredSensorsListProps {
  sensors: DataSourceItem[];
  onRemove: (sensorId: string) => void;
  onEdit?: (sensor: DataSourceItem) => void;
}

export const RegisteredSensorsList: React.FC<RegisteredSensorsListProps> = ({
  sensors,
  onRemove,
  onEdit,
}) => {
  const { t } = useTranslation();
  const edges = useTopologyStore((s) => s.edges);
  const nodes = useTopologyStore((s) => s.nodes);

  const getElementDisplayName = (elementId?: string, fallbackName?: string | null) => {
    if (!elementId) return '';
    const edge = edges.find(
      (e) =>
        e.id === elementId ||
        `-${e.id}` === elementId ||
        e.id === elementId.replace(/^-/, '')
    );
    if (edge?.name) return edge.name;
    const node = nodes.find((n) => n.id === elementId);
    if (node?.name) return node.name;
    return fallbackName || elementId;
  };

  return (
    <div className="space-y-2 pt-2">
      <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
        {t('wizard.registeredSensors')} ({sensors.length})
      </span>
      {sensors.length === 0 ? (
        <div className="p-3 border border-dashed border-border rounded-xl text-center text-slate-400 dark:text-slate-500 text-xs">
          Nenhum sensor cadastrado até o momento.
        </div>
      ) : (
        <div className="space-y-1.5 max-h-36 overflow-y-auto pr-1">
          {sensors.map((src) => (
            <div
              key={src.id}
              className="p-2 rounded-lg bg-surface dark:bg-background/80 border border-border flex items-center justify-between shadow-xs"
            >
              <div className="flex items-center gap-2 min-w-0">
                <Radio
                  className={`w-3.5 h-3.5 flex-shrink-0 ${
                    src.is_local ? 'text-accent-cyan' : 'text-primary-500 dark:text-primary-400'
                  }`}
                />
                <div className="min-w-0">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="font-medium text-slate-800 dark:text-slate-200 truncate text-xs">
                      {src.name}
                    </span>
                    <span className="text-[10px] font-mono text-slate-400 dark:text-slate-500">
                      ({src.id})
                    </span>
                  </div>
                  {src.associated_element && (
                    <p
                      className="text-[10px] text-accent-cyan font-mono truncate"
                      title={`ID SUMO: ${src.associated_element}`}
                    >
                      ↳ Via monitorada:{' '}
                      <span className="font-semibold">
                        {getElementDisplayName(src.associated_element, src.associated_element_name)}
                      </span>
                    </p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span
                  className={`text-[9px] font-bold px-2 py-0.5 rounded border ${
                    src.is_local
                      ? 'bg-accent-cyan/10 text-accent-cyan border-accent-cyan/30'
                      : 'bg-primary-500/10 text-primary-600 dark:text-primary-400 border-primary-500/30'
                  }`}
                >
                  {src.is_local ? 'LOCAL' : 'GLOBAL'}
                </span>
                {onEdit && (
                  <button
                    type="button"
                    onClick={() => onEdit(src)}
                    className="p-1 text-slate-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors cursor-pointer"
                    title="Editar Sensor"
                  >
                    <Pencil className="w-3.5 h-3.5" />
                  </button>
                )}
                <button
                  type="button"
                  onClick={() => onRemove(src.id)}
                  className="p-1 text-slate-400 hover:text-rose-600 dark:hover:text-rose-400 transition-colors cursor-pointer"
                  title="Remover Sensor"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
