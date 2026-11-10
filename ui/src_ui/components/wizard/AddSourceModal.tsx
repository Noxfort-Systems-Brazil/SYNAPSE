// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { useTranslation } from 'react-i18next';
import { PlusCircle, ArrowLeft, X } from 'lucide-react';
import { BatchImportModal } from './BatchImportModal';
import { useTopologyStore } from '../../stores';
import { useAddSourceForm, SourceTypeSelector, SourceConfigForm } from './add_source';

interface AddSourceModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AddSourceModal: React.FC<AddSourceModalProps> = ({ isOpen, onClose }) => {
  const { t } = useTranslation();
  const isPickingElement = useTopologyStore((s) => s.isPickingElement);

  const form = useAddSourceForm(isOpen, onClose);

  if (!isOpen) return null;

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in select-none ${
        isPickingElement ? 'hidden pointer-events-none opacity-0' : ''
      }`}
    >
      <div className="w-full max-w-xl glass-panel bg-surface p-6 rounded-2xl shadow-2xl border border-border space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border/80 pb-4">
          <h2 className="text-base font-bold text-slate-900 dark:text-white tracking-tight flex items-center gap-2">
            <PlusCircle className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
            <span>Assistente de Cadastro de Nova Fonte</span>
          </h2>
          <button
            onClick={form.handleClose}
            className="p-1.5 rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-surfaceHover transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* STEP 1: Select Type */}
        {form.step === 1 && (
          <SourceTypeSelector
            onSelectType={(type) => {
              form.setSourceType(type);
              form.setStep(2);
            }}
            onOpenBatchModal={() => form.setIsBatchModalOpen(true)}
            isDuckDnsActive={form.isDuckDnsActive}
          />
        )}

        {/* STEP 2: Configuration */}
        {form.step === 2 && (
          <SourceConfigForm
            sourceType={form.sourceType}
            sourceName={form.sourceName}
            setSourceName={form.setSourceName}
            selectedLocation={form.selectedLocation}
            setSelectedLocation={form.setSelectedLocation}
            globalUrl={form.globalUrl}
            setGlobalUrl={form.setGlobalUrl}
            localIp={form.localIp}
            gatewayPort={form.gatewayPort}
            sourceId={form.sourceId}
            copiedField={form.copiedField}
            onCopy={form.handleCopy}
            ingressUrl={form.ingressUrl}
          />
        )}

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-border/80 pt-4">
          {form.step === 2 ? (
            <button
              onClick={() => form.setStep(1)}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white flex items-center gap-1.5"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Voltar</span>
            </button>
          ) : (
            <div />
          )}

          <div className="flex items-center gap-2">
            <button
              onClick={form.handleClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-700 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors"
            >
              {t('settings.cancel')}
            </button>

            {form.step === 2 && (
              <button
                onClick={form.handleRegister}
                disabled={!form.sourceName.trim()}
                className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white text-xs font-bold shadow-md shadow-emerald-600/30 transition-all"
              >
                Concluir & Registrar
              </button>
            )}
          </div>
        </div>
      </div>

      <BatchImportModal
        isOpen={form.isBatchModalOpen}
        onClose={() => {
          form.setIsBatchModalOpen(false);
          onClose();
        }}
      />
    </div>
  );
};
