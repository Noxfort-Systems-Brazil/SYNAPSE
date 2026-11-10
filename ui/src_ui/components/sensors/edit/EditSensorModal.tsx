// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { Pencil, X } from 'lucide-react';
import { DataSourceItem } from '../../../types/sensors';
import { useEditSensorForm } from './useEditSensorForm';
import { EditSensorForm } from './EditSensorForm';

export interface EditSensorModalProps {
  isOpen: boolean;
  sensor: DataSourceItem | null;
  onClose: () => void;
  onSaved?: () => void;
}

/**
 * Architectural Layout Composer (SOLID: Open/Closed & Dependency Inversion)
 * Connects the Application Hook (useEditSensorForm) with the Presentational Form (EditSensorForm)
 * inside a modal dialog window.
 */
export const EditSensorModal: React.FC<EditSensorModalProps> = ({
  isOpen,
  sensor,
  onClose,
  onSaved,
}) => {
  const form = useEditSensorForm(isOpen, sensor, onClose, onSaved);

  if (!isOpen || !sensor) return null;

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in select-none ${
        form.isPickingElement ? 'hidden pointer-events-none opacity-0' : ''
      }`}
    >
      <div className="w-full max-w-lg bg-surface dark:bg-surfaceElevated border border-border p-6 rounded-2xl shadow-2xl space-y-5 animate-in zoom-in-95">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border/80 pb-3.5">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-primary-500/10 border border-primary-500/20 text-primary-500 dark:text-primary-400">
              <Pencil className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <span>Modificar Sensor</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 font-normal">
                  {sensor.id}
                </span>
              </h2>
              <p className="text-[11px] text-slate-500 dark:text-slate-400">
                Altere os parâmetros de rede, via viária e metadados desta fonte.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Presentational Form */}
        <EditSensorForm
          name={form.name}
          setName={form.setName}
          isLocal={form.isLocal}
          setIsLocal={form.setIsLocal}
          sourceType={form.sourceType}
          setSourceType={form.setSourceType}
          connectionString={form.connectionString}
          setConnectionString={form.setConnectionString}
          location={form.location}
          setLocation={form.setLocation}
          isSaving={form.isSaving}
          errorMsg={form.errorMsg}
          edges={form.edges}
          nodes={form.nodes}
          onPickOnMap={form.handlePickOnMap}
          onSave={form.handleSave}
          onCancel={onClose}
        />
      </div>
    </div>
  );
};
