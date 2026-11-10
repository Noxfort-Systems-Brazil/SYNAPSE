// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { PlusCircle, Download } from 'lucide-react';
import { useSensorsStore, useTopologyStore, useSecurityStore } from '../../../stores';
import { sensorService } from '../../../services/api';
import { SensorItemRow } from './SensorItemRow';
import { EditSensorModal } from '../../sensors/edit';
import { DataSourceItem } from '../../../types/sensors';
import { exportLocalSensorsCsv } from '../../../utils/batchCsvUtils';

interface SensorListSectionProps {
  openImportWizard: (step?: 1 | 2 | 3) => void;
  setActiveTab: (tab: 'map' | 'dashboard' | 'xai') => void;
  disabled?: boolean;
}

/**
 * Single Responsibility Principle (SRP):
 * Manages the presentation, filtering, and user interactions for registered IoT data sources.
 */
export const SensorListSection: React.FC<SensorListSectionProps> = ({
  openImportWizard,
  setActiveTab,
  disabled = false,
}) => {
  const { t } = useTranslation();
  const sources = useSensorsStore((s) => s.sources);
  const setAssociatingSourceId = useTopologyStore((s) => s.setAssociatingSourceId);
  const requestAuth = useSecurityStore((s) => s.requestAuth);

  const [activeMenuSourceId, setActiveMenuSourceId] = useState<string | null>(null);
  const [editingSensor, setEditingSensor] = useState<DataSourceItem | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  // Live IoT sensors (excluding SUMO map elements and parquet historical dataset)
  const liveSensors = sources.filter(
    (s) =>
      s.source_type !== 'SUMO Network' &&
      s.id !== 'map_main' &&
      s.source_type !== 'Parquet' &&
      s.id !== 'historical_base'
  );

  const localSensors = liveSensors.filter((s) => s.is_local);
  const hasLocalSensors = localSensors.length > 0;

  const handleExport = async () => {
    if (isExporting || !hasLocalSensors) return;
    setIsExporting(true);
    try {
      await exportLocalSensorsCsv(sources);
    } finally {
      setIsExporting(false);
    }
  };

  const handleStartReassociation = (sourceId: string) => {
    setActiveTab('map');
    setAssociatingSourceId(sourceId);
    setActiveMenuSourceId(null);
  };

  const handleRemoveSource = (sourceId: string) => {
    requestAuth(async () => {
      await sensorService.removeSource(sourceId);
    });
    setActiveMenuSourceId(null);
  };

  const handleToggleOrigin = async (sourceId: string) => {
    await sensorService.toggleOrigin(sourceId);
  };

  return (
    <div className="space-y-2 pt-2">
      <div className="flex items-center justify-between px-1">
        <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
          {t('controls.sourcesTitle')} ({liveSensors.length})
        </span>
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={handleExport}
            disabled={disabled || !hasLocalSensors || isExporting}
            title={
              !hasLocalSensors
                ? 'Nenhum sensor local para exportar'
                : `Exportar Sensores Locais (CSV) (${localSensors.length})`
            }
            className={`p-1 rounded-lg text-slate-500 dark:text-slate-400 hover:text-emerald-500 dark:hover:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-950/40 transition-colors ${
              disabled || !hasLocalSensors || isExporting
                ? 'opacity-40 cursor-not-allowed'
                : 'cursor-pointer'
            }`}
          >
            <Download className="w-3.5 h-3.5" />
          </button>
          <button
            type="button"
            onClick={() => openImportWizard(3)}
            disabled={disabled}
            title="Adicionar Sensor"
            className={`p-1 rounded-lg text-slate-500 dark:text-slate-400 hover:text-emerald-500 dark:hover:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-950/40 transition-colors ${
              disabled ? 'opacity-50 pointer-events-none' : ''
            }`}
          >
            <PlusCircle className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {liveSensors.length === 0 ? (
        <div
          onClick={() => {
            if (!disabled) openImportWizard(1);
          }}
          className={`p-4 border border-dashed border-border rounded-xl text-center text-xs text-slate-500 dark:text-slate-400 hover:border-primary-500/40 hover:text-slate-700 dark:hover:text-slate-300 transition-all ${
            disabled ? 'opacity-50 pointer-events-none' : 'cursor-pointer'
          }`}
        >
          {t('controls.noSources')}
        </div>
      ) : (
        <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
          {liveSensors.map((src) => (
            <SensorItemRow
              key={src.id}
              sensor={src}
              isMenuOpen={activeMenuSourceId === src.id}
              onToggleMenu={() =>
                setActiveMenuSourceId(activeMenuSourceId === src.id ? null : src.id)
              }
              onToggleOrigin={handleToggleOrigin}
              onStartReassociation={handleStartReassociation}
              onRemoveSource={handleRemoveSource}
              onEditSensor={(sensor) => {
                setActiveMenuSourceId(null);
                setEditingSensor(sensor);
              }}
              disabled={disabled}
            />
          ))}
        </div>
      )}

      {/* Sensor Modification / Edit Modal */}
      <EditSensorModal
        isOpen={!!editingSensor}
        sensor={editingSensor}
        onClose={() => setEditingSensor(null)}
      />
    </div>
  );
};
