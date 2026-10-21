// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import tokensData from './tokens.json';

export type ThemeMode = 'dark' | 'light';

export interface DesignTokens {
  name: string;
  version: string;
  typography: {
    fontFamily: {
      sans: string[];
      mono: string[];
    };
  };
  palette: {
    primary: Record<string, string>;
    accents: Record<string, string>;
  };
  themes: {
    light: {
      name: string;
      colors: {
        bg: {
          background: string;
          surface: string;
          surfaceHover: string;
          surfaceElevated: string;
        };
        border: {
          default: string;
          subtle: string;
        };
        text: {
          primary: string;
          secondary: string;
          muted: string;
          subtle: string;
        };
        canvas: {
          background: string;
          roadDefault: string;
          roadActive: string;
          roadMonitored: string;
          roadSelected: string;
          node: string;
          nodeActive: string;
        };
        charts: {
          tooltipBg: string;
          tooltipBorder: string;
          tooltipText: string;
          axisLine: string;
          axisLabel: string;
          splitLine: string;
          yAxisLabel: string;
        };
      };
    };
    dark: {
      name: string;
      colors: {
        bg: {
          background: string;
          surface: string;
          surfaceHover: string;
          surfaceElevated: string;
        };
        border: {
          default: string;
          subtle: string;
        };
        text: {
          primary: string;
          secondary: string;
          muted: string;
          subtle: string;
        };
        canvas: {
          background: string;
          roadDefault: string;
          roadActive: string;
          roadMonitored: string;
          roadSelected: string;
          node: string;
          nodeActive: string;
        };
        charts: {
          tooltipBg: string;
          tooltipBorder: string;
          tooltipText: string;
          axisLine: string;
          axisLabel: string;
          splitLine: string;
          yAxisLabel: string;
        };
      };
    };
  };
}

export const themeTokens = tokensData as unknown as DesignTokens;

/**
 * Retrieves the theme token configuration for a specific mode ('dark' | 'light')
 */
export function getThemeTokens(mode: ThemeMode = 'dark') {
  return themeTokens.themes[mode] || themeTokens.themes.dark;
}

export default themeTokens;
