// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { useSystemStore } from '../../stores';
import { PhaseControlCard } from './sidebar/PhaseControlCard';
import { IngestionWizardCard } from './sidebar/IngestionWizardCard';
import { SensorListSection } from './sidebar/SensorListSection';

export interface SidebarProps {
  openImportWizard: (step?: 1 | 2 | 3) => void;
  setActiveTab: (tab: 'map' | 'dashboard' | 'xai') => void;
}

/**
 * Single Responsibility Principle (SRP) & Open/Closed Principle (OCP):
 * Pure architectural layout composer for the desktop application sidebar.
 * Delegates lifecycle orchestration to PhaseControlCard, ingestion shortcuts
 * to IngestionWizardCard, and sensor management to SensorListSection.
 */
export const Sidebar: React.FC<SidebarProps> = ({ openImportWizard, setActiveTab }) => {
  const phase = useSystemStore((s) => s.phase);
  const isRunningPhase =
    phase === 'RUNNING_OPTIMIZATION' ||
    phase === 'RUNNING_OFFLINE' ||
    phase === 'RUNNING_ONLINE';

  return (
    <aside className="w-80 h-[calc(100vh-4rem-2rem)] border-r border-border bg-surface/60 flex flex-col justify-between select-none">
      <div className="p-4 space-y-4 overflow-y-auto flex-1">
        {/* 1. 3-Phase Lifecycle State Machine Card */}
        <PhaseControlCard openImportWizard={openImportWizard} />

        {/* 2. Unified Ingestion Wizard Shortcut */}
        <IngestionWizardCard
          openImportWizard={openImportWizard}
          disabled={isRunningPhase}
        />

        {/* 3. Data Sources List with Context Menu & Re-association */}
        <SensorListSection
          openImportWizard={openImportWizard}
          setActiveTab={setActiveTab}
          disabled={isRunningPhase}
        />
      </div>
    </aside>
  );
};

export default Sidebar;
