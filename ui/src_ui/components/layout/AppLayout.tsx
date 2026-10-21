// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React, { useState, useEffect } from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { StatusBar } from './StatusBar';
import { LogConsole } from './LogConsole';
import { SumoMapCanvas } from '../map/SumoMapCanvas';
import { LiveDashboard } from '../dashboard/LiveDashboard';
import { XaiInspector } from '../xai/XaiInspector';
import { SettingsModal } from '../settings/SettingsModal';
import { ImportWizardModal } from '../wizard/ImportWizardModal';
import { initSynapseBridge, useTopologyStore } from '../../stores';

export const AppLayout: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'map' | 'dashboard' | 'xai'>('map');
  const [isLogsOpen, setIsLogsOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isImportWizardOpen, setIsImportWizardOpen] = useState(false);
  const [wizardInitialStep, setWizardInitialStep] = useState<1 | 2 | 3>(1);

  const isPickingElement = useTopologyStore((s) => s.isPickingElement);

  // Auto-switch to map view if element picking mode is activated
  useEffect(() => {
    if (isPickingElement && activeTab !== 'map') {
      setActiveTab('map');
    }
  }, [isPickingElement, activeTab]);

  useEffect(() => {
    let unlisten: (() => void) | undefined;
    initSynapseBridge().then((fn) => {
      unlisten = fn;
    });
    return () => {
      if (unlisten) unlisten();
    };
  }, []);

  const handleOpenImportWizard = (step: 1 | 2 | 3 = 1) => {
    setWizardInitialStep(step);
    setIsImportWizardOpen(true);
  };

  return (
    <div className="w-screen h-screen flex flex-col bg-background text-slate-100 overflow-hidden select-none">
      {/* 1. Top Header */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        openSettings={() => setIsSettingsOpen(true)}
        openLogs={() => setIsLogsOpen(!isLogsOpen)}
        isLogsOpen={isLogsOpen}
      />

      {/* 2. Main Work Area (Sidebar + Active View) */}
      <div className="flex-1 flex overflow-hidden relative">
        <Sidebar 
          openImportWizard={handleOpenImportWizard}
          setActiveTab={setActiveTab}
        />

        <main className="flex-1 relative overflow-hidden">
          {activeTab === 'map' && <SumoMapCanvas />}
          {activeTab === 'dashboard' && <LiveDashboard />}
          {activeTab === 'xai' && <XaiInspector />}
        </main>

        {/* Retractable Log Drawer */}
        <LogConsole isOpen={isLogsOpen} onClose={() => setIsLogsOpen(false)} />
      </div>

      {/* 3. Bottom Status Bar */}
      <StatusBar />

      {/* 4. Modals */}
      <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
      
      <ImportWizardModal 
        isOpen={isImportWizardOpen} 
        onClose={() => setIsImportWizardOpen(false)} 
        initialStep={wizardInitialStep}
      />
    </div>
  );
};
