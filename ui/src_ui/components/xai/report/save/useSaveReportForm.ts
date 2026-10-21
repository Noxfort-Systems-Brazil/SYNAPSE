// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { useState, useEffect } from 'react';
import { systemService } from '../../../../services/api/SystemService';
import {
  SaveLocationType,
  UseSaveReportFormReturn,
  ReportPathResolver,
} from './types';

/**
 * Application / Controller Hook (SOLID: Single Responsibility & Dependency Inversion).
 * Encapsulates the save workflow, form lifecycle, validation rules, and system dialog coordination.
 */
export function useSaveReportForm(
  isOpen: boolean,
  defaultFilename: string,
  onSave: (outputPath?: string) => Promise<boolean | void>,
  onClose: () => void
): UseSaveReportFormReturn {
  const [filename, setFilenameState] = useState(defaultFilename);
  const [saveLocationType, setSaveLocationType] = useState<SaveLocationType>('downloads');
  const [customDirectory, setCustomDirectory] = useState<string>('');
  const [isPickingDir, setIsPickingDir] = useState(false);
  const [isPickingNative, setIsPickingNative] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  // Synchronize defaultFilename whenever the modal opens or defaultFilename updates
  useEffect(() => {
    if (isOpen) {
      setFilenameState(defaultFilename);
      setValidationError(null);
    }
  }, [isOpen, defaultFilename]);

  const setFilename = (name: string) => {
    setFilenameState(name);
    if (validationError) {
      setValidationError(null);
    }
  };

  const handleResetFilename = () => {
    setFilenameState(defaultFilename);
    setValidationError(null);
  };

  const handlePickDirectory = async () => {
    setIsPickingDir(true);
    try {
      const res = await systemService.pickDirectory({
        title: 'Selecionar Pasta para Salvar o Laudo Técnico',
      });
      if (res.path && !res.cancelled) {
        setCustomDirectory(res.path);
        setSaveLocationType('custom');
        setValidationError(null);
      }
    } catch (err) {
      console.error('[useSaveReportForm] Erro ao selecionar diretório:', err);
    } finally {
      setIsPickingDir(false);
    }
  };

  const handleNativeSaveDialog = async () => {
    setIsPickingNative(true);
    try {
      const cleanName = ReportPathResolver.ensureDocxExtension(filename);
      const res = await systemService.saveFile({
        defaultFilename: cleanName,
        title: 'Salvar Laudo Técnico Oficial (.docx)',
        filterName: 'Documento Word (*.docx)',
        extensions: ['docx'],
      });

      if (res.path && !res.cancelled) {
        await onSave(res.path);
        onClose();
      }
    } catch (err) {
      console.error('[useSaveReportForm] Erro no diálogo nativo de salvamento:', err);
    } finally {
      setIsPickingNative(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const error = ReportPathResolver.validate(filename, saveLocationType, customDirectory);
    if (error) {
      setValidationError(error);
      return;
    }

    const cleanFilename = ReportPathResolver.ensureDocxExtension(filename);

    if (saveLocationType === 'custom') {
      const fullPath = ReportPathResolver.resolveFullPath(customDirectory, cleanFilename);
      await onSave(fullPath);
      onClose();
    } else {
      // Saves to default Downloads with custom or default filename
      await onSave(cleanFilename);
      onClose();
    }
  };

  return {
    filename,
    setFilename,
    saveLocationType,
    setSaveLocationType,
    customDirectory,
    isPickingDir,
    isPickingNative,
    validationError,
    handleResetFilename,
    handlePickDirectory,
    handleNativeSaveDialog,
    handleSubmit,
  };
}
