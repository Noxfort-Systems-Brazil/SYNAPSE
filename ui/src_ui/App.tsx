// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React, { useEffect } from 'react';
import { AppLayout } from './components/layout/AppLayout';
import { SecurityModal } from './components/security/SecurityModal';
import { LockdownOverlay } from './components/security/LockdownOverlay';
import { useSystemStore, useSecurityStore } from './stores';
import { toggleFullscreen } from './utils/windowControls';
import { systemService } from './services/api';

export const App: React.FC = () => {
  const theme = useSystemStore((s) => s.theme);
  const checkLockdown = useSecurityStore((s) => s.checkLockdown);
  const setLockedDown = useSecurityStore((s) => s.setLockedDown);

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
      root.classList.remove('light');
    } else {
      root.classList.add('light');
      root.classList.remove('dark');
    }
  }, [theme]);

  // Global F11 shortcut listener for fullscreen toggle
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'F11') {
        e.preventDefault();
        toggleFullscreen();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Restore database connection state from settings.ini on application startup
  useEffect(() => {
    (async () => {
      try {
        const dbCfg = await systemService.getDatabaseConfig();
        if (dbCfg?.connected) {
          useSystemStore.getState().setDbStatus({
            connected: true,
            message: `Conectado ao schema '${dbCfg.schema || 'schema_synapse'}'`,
          });
        } else {
          useSystemStore.getState().setDbStatus({
            connected: false,
            message: 'Desconectado',
          });
        }
      } catch (e) {
        console.warn('Initial config sync skipped:', e);
      }
    })();
  }, []);

  // Security lockdown listener and initialization
  useEffect(() => {
    checkLockdown();

    let unlisten: (() => void) | undefined;
    (async () => {
      try {
        const { securityService } = await import('./services/api');
        unlisten = await securityService.onLockdownEvent((data) => {
          setLockedDown(Boolean(data?.active));
        });
      } catch (err) {
        console.warn('Could not initialize lockdown event listener:', err);
      }
    })();

    return () => {
      if (unlisten) unlisten();
    };
  }, [checkLockdown, setLockedDown]);

  return (
    <>
      <AppLayout />
      <SecurityModal />
      <LockdownOverlay />
    </>
  );
};

export default App;

