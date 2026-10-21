// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { ITransportClient } from './ITransportClient';
import { TauriTransportClient } from './TauriTransportClient';

export * from './ITransportClient';
export * from './TauriTransportClient';

let clientInstance: ITransportClient | null = null;

export function isTauriEnvironment(): boolean {
  if (typeof window === 'undefined') return false;
  return Boolean(
    (window as any).__TAURI_INTERNALS__ ||
    (window as any).__TAURI__ ||
    (window as any).__TAURI_IPC__
  );
}

export function getTransportClient(): ITransportClient {
  if (!clientInstance) {
    clientInstance = new TauriTransportClient();
  }
  return clientInstance;
}

export function setTransportClient(customClient: ITransportClient) {
  clientInstance = customClient;
}
