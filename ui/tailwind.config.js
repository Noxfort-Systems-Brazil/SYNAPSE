// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import tokens from './src_ui/theme/tokens.json';

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src_ui/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: tokens.typography?.fontFamily?.sans || ['Plus Jakarta Sans', 'sans-serif'],
        mono: tokens.typography?.fontFamily?.mono || ['JetBrains Mono', 'monospace'],
      },
      colors: {
        background: "var(--bg-background)",
        surface: "var(--bg-surface)",
        surfaceHover: "var(--bg-surface-hover)",
        surfaceElevated: "var(--bg-surface-elevated)",
        border: "var(--border-color)",
        borderSubtle: "var(--border-subtle)",
        // Semantic text tokens mapped to CSS custom properties
        textPrimary: "var(--text-primary)",
        textSecondary: "var(--text-secondary)",
        textMuted: "var(--text-muted)",
        textSubtle: "var(--text-subtle)",
        primary: tokens.palette.primary,
        accent: tokens.palette.accents,
      },
    },
  },
  plugins: [],
}
