// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

/**
 * Domain & Architecture Contracts for the Official Report Save Module.
 * Follows DDD (Domain-Driven Design), Clean Architecture, and SOLID principles.
 */

export type SaveLocationType = 'downloads' | 'custom';

export interface SaveReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (outputPath?: string) => Promise<boolean | void>;
  isSaving: boolean;
  defaultFilename: string;
  protocol?: string;
}

export interface UseSaveReportFormReturn {
  filename: string;
  setFilename: (name: string) => void;
  saveLocationType: SaveLocationType;
  setSaveLocationType: (type: SaveLocationType) => void;
  customDirectory: string;
  isPickingDir: boolean;
  isPickingNative: boolean;
  validationError: string | null;
  handleResetFilename: () => void;
  handlePickDirectory: () => Promise<void>;
  handleNativeSaveDialog: () => Promise<void>;
  handleSubmit: (e: React.FormEvent) => Promise<void>;
}

export interface SaveReportHeaderProps {
  protocol?: string;
  onClose: () => void;
  isDisabled: boolean;
}

export interface SaveReportFilenameFieldProps {
  filename: string;
  defaultFilename: string;
  onFilenameChange: (name: string) => void;
  onResetFilename: () => void;
  isDisabled: boolean;
}

export interface SaveReportLocationPickerProps {
  saveLocationType: SaveLocationType;
  onLocationTypeChange: (type: SaveLocationType) => void;
  customDirectory: string;
  isPickingDir: boolean;
  onPickDirectory: () => Promise<void>;
  isDisabled: boolean;
}

export interface SaveReportNativeButtonProps {
  isPickingNative: boolean;
  onNativeSaveDialog: () => Promise<void>;
  isDisabled: boolean;
}

export interface SaveReportActionButtonsProps {
  isSaving: boolean;
  isDisabled: boolean;
  onCancel: () => void;
}

/**
 * Domain Service / Value Object: ReportPathResolver
 * Encapsulates file naming invariants and platform filesystem path composition.
 */
export class ReportPathResolver {
  public static ensureDocxExtension(filename: string): string {
    const trimmed = filename.trim();
    if (!trimmed) return 'laudo.docx';
    return trimmed.toLowerCase().endsWith('.docx') ? trimmed : `${trimmed}.docx`;
  }

  public static sanitizeFilename(name: string): string {
    // Strips invalid OS characters: <>:"/\|?* and control characters
    return name.replace(/[<>:"/\\|?*\x00-\x1F]/g, '_').trim();
  }

  public static resolveFullPath(directory: string, filename: string): string {
    const cleanDir = directory.trim().replace(/[\\/]+$/, '');
    const cleanName = this.ensureDocxExtension(filename);
    const separator = cleanDir.includes('\\') ? '\\' : '/';
    return `${cleanDir}${separator}${cleanName}`;
  }

  public static validate(
    filename: string,
    locationType: SaveLocationType,
    customDirectory: string
  ): string | null {
    const trimmed = filename.trim();
    if (!trimmed) {
      return 'Por favor, informe um nome válido para o arquivo do laudo.';
    }

    if (locationType === 'custom') {
      const trimmedDir = customDirectory.trim();
      if (!trimmedDir) {
        return 'Por favor, selecione uma pasta de destino ou opte por salvar na pasta Downloads.';
      }
    }

    return null;
  }
}
