// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React, { useRef, useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useTranslation } from 'react-i18next';
import { Radio, MoreVertical, Crosshair, Trash2, Pencil } from 'lucide-react';
import { DataSourceItem } from '../../../types/sensors';
import { useTopologyStore } from '../../../stores';

interface SensorItemRowProps {
  sensor: DataSourceItem;
  isMenuOpen: boolean;
  onToggleMenu: () => void;
  onToggleOrigin: (sourceId: string) => void;
  onStartReassociation: (sourceId: string) => void;
  onRemoveSource: (sourceId: string) => void;
  onEditSensor: (sensor: DataSourceItem) => void;
  disabled?: boolean;
}

/**
 * Single Responsibility Principle (SRP):
 * Renders an individual sensor row with origin toggle, topology association link,
 * and context actions dropdown with portal rendering to prevent clipping.
 */
export const SensorItemRow: React.FC<SensorItemRowProps> = ({
  sensor,
  isMenuOpen,
  onToggleMenu,
  onToggleOrigin,
  onStartReassociation,
  onRemoveSource,
  onEditSensor,
  disabled = false,
}) => {
  const { t } = useTranslation();
  const buttonRef = useRef<HTMLButtonElement | null>(null);
  const edges = useTopologyStore((s) => s.edges);
  const nodes = useTopologyStore((s) => s.nodes);

  const assocElem = sensor.associated_element;
  const matchedEdge = assocElem
    ? edges.find(
        (e) =>
          e.id === assocElem ||
          `-${e.id}` === assocElem ||
          e.id === assocElem.replace(/^-/, '')
      )
    : null;
  const matchedNode =
    assocElem && !matchedEdge
      ? nodes.find((n) => n.id === assocElem)
      : null;
  const displayLocation =
    matchedEdge?.name ||
    matchedNode?.name ||
    sensor.associated_element_name ||
    assocElem;

  const [coords, setCoords] = useState<{ top?: number; bottom?: number; right: number }>({
    right: 0,
  });

  useEffect(() => {
    if (isMenuOpen && buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      const menuHeight = 135;
      const spaceBelow = window.innerHeight - rect.bottom;
      const openUpwards = spaceBelow < menuHeight + 20;

      setCoords({
        top: openUpwards ? undefined : rect.bottom + 6,
        bottom: openUpwards ? window.innerHeight - rect.top + 6 : undefined,
        right: Math.max(12, window.innerWidth - rect.right),
      });
    }
  }, [isMenuOpen]);

  return (
    <div
      className={`p-2.5 rounded-lg bg-background/80 border border-border flex items-center justify-between group hover:border-slate-400 dark:hover:border-slate-700 transition-all relative ${
        disabled ? 'opacity-60 pointer-events-none' : ''
      }`}
    >
      <div className="flex items-center gap-2 min-w-0">
        <Radio
          className={`w-3.5 h-3.5 flex-shrink-0 ${
            sensor.is_local ? 'text-accent-cyan' : 'text-primary-500 dark:text-primary-400'
          }`}
        />
        <div className="min-w-0">
          <p className="text-xs font-medium text-slate-800 dark:text-slate-200 truncate" title={sensor.name}>
            {sensor.name}
          </p>
          {sensor.is_local && sensor.associated_element && (
            <p
              className="text-[9px] text-accent-cyan font-mono truncate"
              title={`Elemento SUMO ID: ${sensor.associated_element}`}
            >
              ↳ Via: {displayLocation}
            </p>
          )}
          {!sensor.is_local && (
            <p
              className="text-[9px] text-primary-500 dark:text-primary-400 font-mono truncate"
              title={sensor.connection_string || 'Feed Global (API Externa)'}
            >
              ↳ Feed Global (Pull)
            </p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-1.5 flex-shrink-0">
        <button
          type="button"
          onClick={() => onToggleOrigin(sensor.id)}
          title={t('controls.toggleOrigin')}
          className={`text-[10px] font-bold px-2 py-0.5 rounded border transition-all ${
            sensor.is_local
              ? 'bg-accent-cyan/10 text-accent-cyan border-accent-cyan/30'
              : 'bg-primary-500/10 text-primary-600 dark:text-primary-400 border-primary-500/30'
          }`}
        >
          {sensor.is_local ? t('controls.local') : t('controls.global')}
        </button>

        {/* Options Dropdown Trigger */}
        <div className="relative">
          <button
            ref={buttonRef}
            type="button"
            onClick={onToggleMenu}
            className="p-1 text-slate-400 hover:text-slate-800 dark:hover:text-white rounded hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            title="Mais opções"
          >
            <MoreVertical className="w-3.5 h-3.5" />
          </button>

          {/* Unclipped Portal-based Dropdown */}
          {isMenuOpen &&
            createPortal(
              <>
                <div
                  className="fixed inset-0 z-40 bg-transparent"
                  onClick={onToggleMenu}
                />
                <div
                  className="fixed w-44 bg-surface dark:bg-surfaceElevated border border-border rounded-xl shadow-2xl p-1 z-50 space-y-0.5 animate-in fade-in-50 zoom-in-95 select-none"
                  style={{
                    top: coords.top !== undefined ? `${coords.top}px` : 'auto',
                    bottom: coords.bottom !== undefined ? `${coords.bottom}px` : 'auto',
                    right: `${coords.right}px`,
                  }}
                >
                  <button
                    type="button"
                    onClick={() => {
                      onToggleMenu();
                      onEditSensor(sensor);
                    }}
                    className="w-full px-2.5 py-1.5 text-left text-xs font-medium text-slate-700 dark:text-slate-200 hover:bg-primary-50 dark:hover:bg-primary-950/40 hover:text-primary-600 dark:hover:text-primary-400 rounded-lg flex items-center gap-2 transition-colors cursor-pointer"
                  >
                    <Pencil className="w-3.5 h-3.5 text-primary-500 dark:text-primary-400" />
                    <span>Modificar / Editar</span>
                  </button>

                  {sensor.is_local && (
                    <button
                      type="button"
                      onClick={() => {
                        onToggleMenu();
                        onStartReassociation(sensor.id);
                      }}
                      className="w-full px-2.5 py-1.5 text-left text-xs font-medium text-slate-700 dark:text-slate-200 hover:bg-accent-cyan/10 hover:text-accent-cyan rounded-lg flex items-center gap-2 transition-colors cursor-pointer"
                    >
                      <Crosshair className="w-3.5 h-3.5 text-accent-cyan" />
                      <span>Vincular no Mapa</span>
                    </button>
                  )}

                  <button
                    type="button"
                    onClick={() => {
                      onToggleMenu();
                      onRemoveSource(sensor.id);
                    }}
                    className="w-full px-2.5 py-1.5 text-left text-xs font-medium text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 rounded-lg flex items-center gap-2 transition-colors cursor-pointer"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Remover Sensor</span>
                  </button>
                </div>
              </>,
              document.body
            )}
        </div>
      </div>
    </div>
  );
};
