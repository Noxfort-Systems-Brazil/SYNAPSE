// SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
// Copyright (C) 2026 Noxfort Systems
//
// File: ui/src_ui/components/settings/tabs/DatabaseSettingsTab.tsx
// Author: Gabriel Moraes
// Date: 2026-08-29

import React from 'react';
import {
  useDatabaseSettings,
  DatabaseStatusHeader,
  DatabaseConnectionForm,
  DatabaseActionButtons,
} from './database';

export const DatabaseSettingsTab: React.FC = () => {
  const db = useDatabaseSettings();

  return (
    <div className="space-y-4 text-xs">
      <DatabaseStatusHeader isConnected={db.isConnected} />

      <DatabaseConnectionForm
        dbHost={db.dbHost}
        setDbHost={db.setDbHost}
        dbPort={db.dbPort}
        setDbPort={db.setDbPort}
        dbName={db.dbName}
        setDbName={db.setDbName}
        dbSchema={db.dbSchema}
        setDbSchema={db.setDbSchema}
        dbUser={db.dbUser}
        setDbUser={db.setDbUser}
        dbPass={db.dbPass}
        setDbPass={db.setDbPass}
        dbRootPass={db.dbRootPass}
        setDbRootPass={db.setDbRootPass}
        onFieldChange={db.handleFieldChange}
      />

      <DatabaseActionButtons
        isConnected={db.isConnected}
        isSetupDone={db.isSetupDone}
        dbLoading={db.dbLoading}
        dbFeedback={db.dbFeedback}
        onConnect={db.handleConnect}
        onDisconnect={db.handleDisconnect}
        onInitializeDb={db.handleInitializeDb}
      />
    </div>
  );
};
