// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { ReportTypographyOptions, DEFAULT_REPORT_TYPOGRAPHY } from '../types/report';

interface ReportTypographyState extends ReportTypographyOptions {
  setFontFamily: (fontFamily: 'Arial' | 'Times New Roman') => void;
  setFontSize: (fontSize: number) => void;
  setLineSpacing: (lineSpacing: 1.0 | 1.15 | 1.5) => void;
  setAlignment: (alignment: 'justify' | 'left') => void;
  resetDefaults: () => void;
}

export const useReportTypographyStore = create<ReportTypographyState>()(
  persist(
    (set) => ({
      ...DEFAULT_REPORT_TYPOGRAPHY,
      setFontFamily: (fontFamily) => set({ fontFamily }),
      setFontSize: (fontSize) => set({ fontSize }),
      setLineSpacing: (lineSpacing) => set({ lineSpacing }),
      setAlignment: (alignment) => set({ alignment }),
      resetDefaults: () => set({ ...DEFAULT_REPORT_TYPOGRAPHY }),
    }),
    {
      name: 'synapse-report-typography-preferences',
    }
  )
);
