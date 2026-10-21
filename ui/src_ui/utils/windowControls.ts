// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

export async function toggleFullscreen(): Promise<boolean> {
  try {
    const { invoke } = await import('@tauri-apps/api/core');
    const isFs = await invoke<boolean>('toggle_fullscreen');
    return isFs;
  } catch {
    // Fallback for standard web browser preview
    if (!document.fullscreenElement) {
      await document.documentElement.requestFullscreen().catch(() => {});
      return true;
    } else {
      await document.exitFullscreen().catch(() => {});
      return false;
    }
  }
}

export async function minimizeToTray(): Promise<void> {
  try {
    const { invoke } = await import('@tauri-apps/api/core');
    await invoke('minimize_to_tray');
  } catch (err) {
    console.warn('[WindowControls] Minimize to tray unavailable in browser mode:', err);
  }
}

export async function restoreFromTray(): Promise<void> {
  try {
    const { invoke } = await import('@tauri-apps/api/core');
    await invoke('restore_from_tray');
  } catch (err) {
    console.warn('[WindowControls] Restore from tray unavailable in browser mode:', err);
  }
}
