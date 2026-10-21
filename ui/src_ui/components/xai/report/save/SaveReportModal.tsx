// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { SaveReportModalProps } from './types';
import { useSaveReportForm } from './useSaveReportForm';
import { SaveReportHeader } from './SaveReportHeader';
import { SaveReportFilenameField } from './SaveReportFilenameField';
import { SaveReportLocationPicker } from './SaveReportLocationPicker';
import { SaveReportNativeButton } from './SaveReportNativeButton';
import { SaveReportActionButtons } from './SaveReportActionButtons';

/**
 * Architectural Layout Composer (SOLID: Open/Closed Principle & Dependency Inversion)
 * Connects the application hook (useSaveReportForm) with presentational subcomponents
 * within a modal dialog window.
 */
export const SaveReportModal: React.FC<SaveReportModalProps> = ({
  isOpen,
  onClose,
  onSave,
  isSaving,
  defaultFilename,
  protocol,
}) => {
  const form = useSaveReportForm(isOpen, defaultFilename, onSave, onClose);

  if (!isOpen) return null;

  const isControlsDisabled = isSaving || form.isPickingDir || form.isPickingNative;

  return (
    <div className="fixed inset-0 z-60 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 animate-in fade-in duration-150 select-none">
      <div className="relative w-full max-w-lg bg-slate-900 border border-slate-700 shadow-2xl rounded-2xl overflow-hidden flex flex-col text-slate-100 animate-in zoom-in-95">
        
        {/* Header (SRP) */}
        <SaveReportHeader
          protocol={protocol}
          onClose={onClose}
          isDisabled={isControlsDisabled}
        />

        {/* Form Body */}
        <form onSubmit={form.handleSubmit} className="p-5 space-y-5">
          {/* Filename Field (SRP) */}
          <SaveReportFilenameField
            filename={form.filename}
            defaultFilename={defaultFilename}
            onFilenameChange={form.setFilename}
            onResetFilename={form.handleResetFilename}
            isDisabled={isControlsDisabled}
          />

          {/* Location Picker (SRP) */}
          <SaveReportLocationPicker
            saveLocationType={form.saveLocationType}
            onLocationTypeChange={form.setSaveLocationType}
            customDirectory={form.customDirectory}
            isPickingDir={form.isPickingDir}
            onPickDirectory={form.handlePickDirectory}
            isDisabled={isControlsDisabled}
          />

          {/* Native OS Dialog Trigger (SRP) */}
          <SaveReportNativeButton
            isPickingNative={form.isPickingNative}
            onNativeSaveDialog={form.handleNativeSaveDialog}
            isDisabled={isControlsDisabled}
          />

          {/* Validation Error Feedback */}
          {form.validationError && (
            <div className="p-2.5 rounded-lg bg-red-500/10 border border-red-500/30 text-red-300 text-xs">
              {form.validationError}
            </div>
          )}

          {/* Footer Action Buttons (SRP) */}
          <SaveReportActionButtons
            isSaving={isSaving}
            isDisabled={isControlsDisabled}
            onCancel={onClose}
          />
        </form>

      </div>
    </div>
  );
};
