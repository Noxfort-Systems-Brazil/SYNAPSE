// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { useState, useEffect, useCallback } from 'react';
import { toggleFullscreen as windowToggleFullscreen, minimizeToTray as windowMinimizeToTray } from '../utils/windowControls';

export interface UseWindowControlsReturn {
  isFullscreen: boolean;
  toggleFullscreen: () => Promise<void>;
  minimizeToTray: () => Promise<void>;
}

/**
 * Hook to abstract and isolate desktop window control (DOM and Tauri/desktop IPC),
 * adhering to the Dependency Inversion Principle (DIP).
 */
export function useWindowControls(): UseWindowControlsReturn {
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    const checkFs = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    document.addEventListener('fullscreenchange', checkFs);
    return () => document.removeEventListener('fullscreenchange', checkFs);
  }, []);

  const toggleFullscreen = useCallback(async () => {
    const nextFs = await windowToggleFullscreen();
    setIsFullscreen(nextFs);
  }, []);

  const minimizeToTray = useCallback(async () => {
    await windowMinimizeToTray();
  }, []);

  return {
    isFullscreen,
    toggleFullscreen,
    minimizeToTray,
  };
}
