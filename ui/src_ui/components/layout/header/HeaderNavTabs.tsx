// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { useTranslation } from 'react-i18next';
import { Network, BarChart3, ShieldCheck } from 'lucide-react';

export type TabId = 'map' | 'dashboard' | 'xai';

export interface HeaderNavTabItem {
  id: TabId;
  labelKey: string;
  shortLabelKey?: string;
  icon: React.ComponentType<{ className?: string }>;
}

export const DEFAULT_NAV_TABS: HeaderNavTabItem[] = [
  { id: 'map', labelKey: 'nav.map', shortLabelKey: 'nav.mapShort', icon: Network },
  { id: 'dashboard', labelKey: 'nav.dashboard', shortLabelKey: 'nav.dashboardShort', icon: BarChart3 },
  { id: 'xai', labelKey: 'nav.xai', shortLabelKey: 'nav.xaiShort', icon: ShieldCheck },
];

interface HeaderNavTabsProps {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
  tabs?: HeaderNavTabItem[];
}

/**
 * Atomic subcomponent for tab navigation with declarative configuration (SRP + OCP).
 */
export const HeaderNavTabs: React.FC<HeaderNavTabsProps> = ({
  activeTab,
  onTabChange,
  tabs = DEFAULT_NAV_TABS,
}) => {
  const { t } = useTranslation();

  return (
    <nav className="flex items-center gap-1 p-1 bg-background/80 border border-border rounded-xl shrink-0">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const isActive = activeTab === tab.id;
        const fullLabel = t(tab.labelKey);
        const shortLabel = tab.shortLabelKey ? t(tab.shortLabelKey) : fullLabel;

        return (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            title={fullLabel}
            aria-label={fullLabel}
            className={`flex items-center gap-1.5 sm:gap-2 px-2.5 sm:px-3 lg:px-4 py-1.5 sm:py-2 rounded-lg text-xs font-semibold transition-all shrink-0 whitespace-nowrap ${
              isActive
                ? 'bg-primary-600 text-white shadow-md shadow-primary-600/20'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-surfaceHover'
            }`}
          >
            <Icon className="w-4 h-4 shrink-0" />
            <span className="hidden lg:inline whitespace-nowrap">{fullLabel}</span>
            <span className="hidden sm:inline lg:hidden whitespace-nowrap">{shortLabel}</span>
          </button>
        );
      })}
    </nav>
  );
};
