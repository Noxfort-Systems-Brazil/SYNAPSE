// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { create } from 'zustand';

export interface MunicipalSettings {
  cityHall: string;
  department: string;
  authorityName: string;
  authorityRole: string;
  registrationNumber: string;
  processPrefix: string;
  logoDataUrl: string | null;
}

interface MunicipalSettingsState extends MunicipalSettings {
  updateSettings: (newSettings: Partial<MunicipalSettings>) => void;
  resetToDefaults: () => void;
  setLogoDataUrl: (url: string | null) => void;
}

const DEFAULT_SETTINGS: MunicipalSettings = {
  cityHall: 'PREFEITURA DO MUNICÍPIO DE SÃO PAULO',
  department: 'SECRETARIA MUNICIPAL DE MOBILIDADE URBANA E TRÂNSITO (SMT)',
  authorityName: 'Gabriel Moraes',
  authorityRole: 'Autoridade Municipal de Trânsito / Secretário de Mobilidade',
  registrationNumber: 'Matrícula Funcional nº 84.102-3 • Portaria de Nomeação SMT nº 142/2025',
  processPrefix: 'PA-SMT-2026/',
  logoDataUrl: null,
};

const STORAGE_KEY = 'synapse_municipal_settings_v3';

const loadSavedSettings = (): MunicipalSettings => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      return { ...DEFAULT_SETTINGS, ...JSON.parse(raw) };
    }
  } catch (e) {
    console.error('Error loading municipal settings from localStorage:', e);
  }
  return DEFAULT_SETTINGS;
};

export const useMunicipalSettingsStore = create<MunicipalSettingsState>((set, get) => ({
  ...loadSavedSettings(),

  updateSettings: (newSettings) => {
    set((state) => {
      const updated = {
        cityHall: newSettings.cityHall ?? state.cityHall,
        department: newSettings.department ?? state.department,
        authorityName: newSettings.authorityName ?? state.authorityName,
        authorityRole: newSettings.authorityRole ?? state.authorityRole,
        registrationNumber: newSettings.registrationNumber ?? state.registrationNumber,
        processPrefix: newSettings.processPrefix ?? state.processPrefix,
        logoDataUrl: newSettings.logoDataUrl !== undefined ? newSettings.logoDataUrl : state.logoDataUrl,
      };
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      } catch (e) {
        console.error('Error persisting municipal settings:', e);
      }
      return updated;
    });
  },

  setLogoDataUrl: (url) => {
    get().updateSettings({ logoDataUrl: url });
  },

  resetToDefaults: () => {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {}
    set({ ...DEFAULT_SETTINGS });
  },
}));
