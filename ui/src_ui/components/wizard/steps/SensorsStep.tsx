// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Radio, Cloud, PlusCircle, CheckCircle2, Layers, Lock } from 'lucide-react';
import { useSensorRegistration } from '../../../hooks/useSensorRegistration';
import { BatchImportModal } from '../BatchImportModal';
import { LocalSensorForm, GlobalSensorForm, RegisteredSensorsList } from '../sensors';
import { EditSensorModal } from '../../sensors/edit';
import { DataSourceItem } from '../../../types/sensors';

/**
 * Step 3: Sensors Registration
 * Refactored to adhere to SOLID principles:
 * - Single Responsibility: Coordinates UI composition; delegation of logic to useSensorRegistration hook.
 * - Open/Closed: Form layouts extracted to subcomponents (LocalSensorForm, GlobalSensorForm, RegisteredSensorsList).
 * - Dependency Inversion: Relies on abstractions and unified hook contract.
 */
export const SensorsStep: React.FC = () => {
  const { t } = useTranslation();
  const {
    sensorType,
    setSensorType,
    sensorName,
    setSensorName,
    selectedLocation,
    setSelectedLocation,
    globalUrl,
    setGlobalUrl,
    localIp,
    gatewayPort,
    isDuckDnsActive,
    ingressUrl,
    sensorId,
    copiedField,
    successMsg,
    isBatchModalOpen,
    setIsBatchModalOpen,
    edges,
    nodes,
    registeredSensors,
    handleCopy,
    handleRegisterSensor,
    handleRemoveSensor,
    handlePickOnMap,
  } = useSensorRegistration();

  const [editingSensor, setEditingSensor] = useState<DataSourceItem | null>(null);

  return (
    <div className="space-y-4 animate-in fade-in">
      {/* Information Header */}
      <div className="p-3.5 bg-emerald-50 dark:bg-emerald-500/10 border border-emerald-200 dark:border-emerald-500/20 rounded-xl text-emerald-800 dark:text-emerald-300 flex items-start justify-between gap-2.5">
        <div className="flex items-start gap-2.5">
          <Radio className="w-4 h-4 text-emerald-600 dark:text-emerald-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-bold text-slate-900 dark:text-white">{t('wizard.sensorsTitle')}</p>
            <p className="text-[11px] text-slate-600 dark:text-slate-300 mt-0.5">{t('wizard.sensorsDesc')}</p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => setIsBatchModalOpen(true)}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-primary-600 hover:bg-primary-700 text-white rounded-lg text-xs font-semibold shadow-sm transition-colors whitespace-nowrap cursor-pointer flex-shrink-0"
        >
          <Layers className="w-3.5 h-3.5" />
          <span>Importar CSV em Lote</span>
        </button>
      </div>

      {/* Sensor Registration Form Card */}
      <div className="p-4 rounded-xl bg-surface dark:bg-background/80 border border-border space-y-4 shadow-sm">
        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={() => {
              if (isDuckDnsActive) setSensorType('LOCAL');
            }}
            disabled={!isDuckDnsActive}
            title={!isDuckDnsActive ? 'DuckDNS é obrigatório para dispositivos locais' : undefined}
            className={`flex-1 py-2 px-3 rounded-xl border text-xs font-bold flex items-center justify-center gap-2 transition-all ${
              !isDuckDnsActive
                ? 'opacity-60 cursor-not-allowed bg-slate-100 dark:bg-slate-800/40 border-slate-300 dark:border-slate-700 text-slate-400'
                : sensorType === 'LOCAL'
                ? 'bg-sky-50 dark:bg-accent-cyan/20 border-accent-cyan text-sky-900 dark:text-white shadow-sm'
                : 'bg-surface border-border text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            {isDuckDnsActive ? (
              <Radio className="w-4 h-4 text-accent-cyan" />
            ) : (
              <Lock className="w-4 h-4 text-amber-500" />
            )}
            <span>{t('wizard.sensorTypeLocal')}</span>
            {!isDuckDnsActive && (
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-600 dark:text-amber-400 font-semibold border border-amber-500/20">
                Requer DuckDNS
              </span>
            )}
          </button>

          <button
            type="button"
            onClick={() => setSensorType('GLOBAL')}
            className={`flex-1 py-2 px-3 rounded-xl border text-xs font-bold flex items-center justify-center gap-2 transition-all ${
              sensorType === 'GLOBAL'
                ? 'bg-primary-50 dark:bg-primary-600/30 border-primary-500 text-primary-900 dark:text-white shadow-sm'
                : 'bg-surface border-border text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <Cloud className="w-4 h-4 text-primary-500 dark:text-primary-400" />
            <span>{t('wizard.sensorTypeGlobal')}</span>
          </button>
        </div>

        <div className="space-y-1.5">
          <label className="text-slate-700 dark:text-slate-300 font-semibold text-xs">
            Nome de Identificação da Fonte:
          </label>
          <input
            type="text"
            placeholder={
              sensorType === 'LOCAL'
                ? 'Ex: Câmera Av. Paulista Norte'
                : 'Ex: Feed Tráfego Waze'
            }
            value={sensorName}
            onChange={(e) => setSensorName(e.target.value)}
            className="w-full h-9 px-3 bg-surface dark:bg-background border border-border rounded-xl text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:border-emerald-500 font-sans text-xs"
          />
        </div>

        {sensorType === 'LOCAL' ? (
          <LocalSensorForm
            selectedLocation={selectedLocation}
            onChangeLocation={setSelectedLocation}
            edges={edges}
            nodes={nodes}
            localIp={localIp}
            gatewayPort={gatewayPort}
            sensorId={sensorId}
            copiedField={copiedField}
            onCopy={handleCopy}
            onPickOnMap={handlePickOnMap}
            ingressUrl={ingressUrl}
            isDuckDnsActive={isDuckDnsActive}
          />
        ) : (
          <GlobalSensorForm
            globalUrl={globalUrl}
            onChangeGlobalUrl={setGlobalUrl}
          />
        )}

        <div className="flex items-center justify-end">
          <button
            type="button"
            onClick={handleRegisterSensor}
            disabled={!sensorName.trim() || (sensorType === 'LOCAL' && !isDuckDnsActive)}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold rounded-xl shadow-md shadow-emerald-600/30 transition-all flex items-center gap-2 cursor-pointer disabled:cursor-not-allowed"
          >
            <PlusCircle className="w-4 h-4" />
            <span>{t('wizard.addAnotherSensor')}</span>
          </button>
        </div>
      </div>

      {/* Success Alert */}
      {successMsg && (
        <div className="p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-500/40 text-emerald-800 dark:text-emerald-300 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span className="text-xs">{successMsg}</span>
        </div>
      )}

      {/* Registered Sources Summary List */}
      <RegisteredSensorsList
        sensors={registeredSensors}
        onRemove={handleRemoveSensor}
        onEdit={(sensor) => setEditingSensor(sensor)}
      />

      <BatchImportModal
        isOpen={isBatchModalOpen}
        onClose={() => setIsBatchModalOpen(false)}
      />

      <EditSensorModal
        isOpen={!!editingSensor}
        sensor={editingSensor}
        onClose={() => setEditingSensor(null)}
      />
    </div>
  );
};
