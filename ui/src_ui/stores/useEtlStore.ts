// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { create } from 'zustand';
import { ParquetInspectionResult, ParquetImportProgress } from '../types/etl';

interface EtlState {
  parquetInspection: ParquetInspectionResult | null;
  importProgress: ParquetImportProgress;
  hasDataset: boolean;

  // Actions
  setHasDataset: (has: boolean) => void;
  setParquetInspection: (result: ParquetInspectionResult | null) => void;
  setImportProgress: (progress: Partial<ParquetImportProgress>) => void;
  resetEtlState: () => void;
}

export const useEtlStore = create<EtlState>((set) => ({
  parquetInspection: null,
  importProgress: { progress: 0, status: '', isImporting: false },
  hasDataset: false,

  setHasDataset: (has) => set({ hasDataset: has }),
  setParquetInspection: (result) => set({ parquetInspection: result }),
  setImportProgress: (progress) =>
    set((state) => {
      const updated = { ...state.importProgress, ...progress };
      return {
        importProgress: updated,
        hasDataset: updated.progress === 100 ? true : state.hasDataset,
      };
    }),
  resetEtlState: () =>
    set({
      parquetInspection: null,
      importProgress: { progress: 0, status: '', isImporting: false },
      hasDataset: false,
    }),
}));
