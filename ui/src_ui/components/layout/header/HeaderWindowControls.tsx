// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { Maximize2, Minimize2, Minus } from 'lucide-react';
import { useWindowControls } from '../../../hooks/useWindowControls';

/**
 * Atomic subcomponent for desktop window controls (Fullscreen and Minimize) (SRP + DIP).
 */
export const HeaderWindowControls: React.FC = () => {
  const { isFullscreen, toggleFullscreen, minimizeToTray } = useWindowControls();

  return (
    <div className="hidden sm:flex items-center gap-1.5 shrink-0">
      <div className="w-[1px] h-5 bg-border mx-0.5 shrink-0" />

      {/* Fullscreen Toggle (F11) */}
      <button
        onClick={toggleFullscreen}
        title={isFullscreen ? 'Sair da Tela Cheia (F11)' : 'Tela Cheia (F11)'}
        className="p-2 rounded-lg bg-surface border border-border text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:border-primary-500/50 transition-all flex items-center justify-center shadow-sm shrink-0"
      >
        {isFullscreen ? (
          <Minimize2 className="w-4 h-4 text-accent-cyan" />
        ) : (
          <Maximize2 className="w-4 h-4" />
        )}
      </button>

      {/* Minimize to Tray */}
      <button
        onClick={minimizeToTray}
        title="Minimizar para a Bandeja"
        className="p-2 rounded-lg bg-surface border border-border text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:border-amber-500/50 transition-all flex items-center justify-center shadow-sm shrink-0"
      >
        <Minus className="w-4 h-4" />
      </button>
    </div>
  );
};
