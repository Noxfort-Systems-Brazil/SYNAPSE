// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { 
  HeaderBrand, 
  HeaderNavTabs, 
  HeaderPhaseBadge, 
  HeaderUserBadge, 
  HeaderQuickActions, 
  HeaderWindowControls,
  TabId 
} from './header';

export interface HeaderProps {
  activeTab: TabId;
  setActiveTab: (tab: TabId) => void;
  openSettings: () => void;
  openLogs: () => void;
  isLogsOpen: boolean;
}

/**
 * Main application header refactored under SOLID principles.
 * Acts solely as a clean orchestrator of layout and composition (SRP).
 */
export const Header: React.FC<HeaderProps> = ({
  activeTab,
  setActiveTab,
  openSettings,
  openLogs,
  isLogsOpen,
}) => {
  return (
    <header className="h-16 border-b border-border bg-surface/90 backdrop-blur-md px-3 sm:px-6 flex items-center justify-between gap-2 sm:gap-4 z-30 select-none overflow-x-auto no-scrollbar">
      {/* 1. Identidade Visual e Marca (SRP) */}
      <HeaderBrand />

      {/* 2. Abas de Navegação (SRP + OCP) */}
      <HeaderNavTabs activeTab={activeTab} onTabChange={setActiveTab} />

      {/* 3. Indicadores de Status e Ações Rápidas (SRP + OCP + DIP) */}
      <div className="flex items-center gap-1.5 sm:gap-2.5 shrink-0">
        <HeaderPhaseBadge />

        <HeaderQuickActions
          openSettings={openSettings}
          openLogs={openLogs}
          isLogsOpen={isLogsOpen}
        >
          <HeaderUserBadge />
        </HeaderQuickActions>

        <HeaderWindowControls />
      </div>
    </header>
  );
};
