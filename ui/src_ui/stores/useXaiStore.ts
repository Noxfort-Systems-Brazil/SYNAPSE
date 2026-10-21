// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { create } from 'zustand';
import { XaiAuditVerdict, LinguistClassification, XaiResultItem } from '../types/xai';

interface XaiState {
  verdicts: XaiAuditVerdict[];
  linguistLogs: LinguistClassification[];
  xaiHistory: XaiResultItem[];
  selectedXaiResultId: string | null;

  // Actions
  addVerdict: (verdict: XaiAuditVerdict) => void;
  addLinguistLog: (log: LinguistClassification) => void;
  addXaiResult: (result: XaiResultItem) => void;
  setSelectedXaiResultId: (id: string | null) => void;
}

export const useXaiStore = create<XaiState>((set) => ({
  verdicts: [],
  linguistLogs: [],
  xaiHistory: [],
  selectedXaiResultId: null,

  addVerdict: (verdict) =>
    set((state) => ({ verdicts: [verdict, ...state.verdicts].slice(0, 100) })),

  addLinguistLog: (log) =>
    set((state) => ({ linguistLogs: [log, ...state.linguistLogs].slice(0, 100) })),

  addXaiResult: (result) =>
    set((state) => ({
      xaiHistory: [result, ...state.xaiHistory].slice(0, 50),
      selectedXaiResultId: result.id,
    })),

  setSelectedXaiResultId: (id) => set({ selectedXaiResultId: id }),
}));
