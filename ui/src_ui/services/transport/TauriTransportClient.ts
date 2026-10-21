// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { ITransportClient, UnlistenFn } from './ITransportClient';

export class TauriTransportClient implements ITransportClient {
  isNativeEnvironment(): boolean {
    if (typeof window === 'undefined') return false;
    return Boolean(
      (window as any).__TAURI_INTERNALS__ ||
      (window as any).__TAURI__ ||
      (window as any).__TAURI_IPC__
    );
  }

  /**
   * Resolves appropriate timeout in milliseconds based on action type and custom override.
   */
  private resolveTimeoutMs(action: string, customTimeoutMs?: number): number {
    if (typeof customTimeoutMs === 'number' && customTimeoutMs > 0) {
      return customTimeoutMs;
    }
    if (action === 'ping') {
      return 5000;
    }
    if (action === 'generate_official_report') {
      return 120000; // 120s (2 min) for SLM / Qwen neural reasoning and document synthesis
    }
    if (action === 'start_offline_bootstrap') {
      return 180000; // 180s (3 min) for offline neural models bootstrap
    }
    if (action === 'export_official_report_docx' || action.startsWith('explain_')) {
      return 60000; // 60s for DOCX disk exports and deep neural XAI explainability
    }
    return 30000; // 30s default for standard actions
  }

  async invoke<TPayload = any, TResponse = any>(
    action: string,
    payload: TPayload = {} as TPayload,
    timeoutMsOverride?: number
  ): Promise<TResponse> {
    const { invoke } = await import('@tauri-apps/api/core');
    const { listen } = await import('@tauri-apps/api/event');
    const id = Math.random().toString(36).substring(2, 9);

    return new Promise<TResponse>(async (resolve, reject) => {
      let unlisten: (() => void) | undefined;
      let unlistenDisconnect: (() => void) | undefined;
      const timeoutMs = this.resolveTimeoutMs(action, timeoutMsOverride);

      const cleanup = () => {
        clearTimeout(timer);
        if (unlisten) unlisten();
        if (unlistenDisconnect) unlistenDisconnect();
      };

      const timer = setTimeout(() => {
        cleanup();
        console.error(`[TauriTransport] ⏱️ Timeout (${timeoutMs}ms) aguardando comando '${action}' (id=${id})`);
        reject(new Error(`Comando '${action}' excedeu o tempo limite (${timeoutMs / 1000}s)`));
      }, timeoutMs);

      try {
        unlisten = await listen<{ id?: string; success?: boolean; result?: any; error?: string }>(
          'synapse:response',
          (event) => {
            if (event.payload?.id === id) {
              cleanup();
              if (event.payload.success === false) {
                console.error(`[TauriTransport] ❌ Comando '${action}' falhou:`, event.payload.error);
                reject(new Error(event.payload.error || 'Command failed'));
              } else {
                console.debug(`[TauriTransport] ✅ Comando '${action}' concluído com sucesso:`, event.payload.result);
                resolve(event.payload.result ?? ({ success: true } as unknown as TResponse));
              }
            }
          }
        );

        unlistenDisconnect = await listen('synapse:disconnected', () => {
          cleanup();
          reject(new Error(`Falha de comunicação: o backend Python foi desconectado antes de responder ao comando '${action}'.`));
        });

        console.debug(`[TauriTransport] 🚀 Enviando comando '${action}' (id=${id}):`, payload);
        await invoke('send_synapse_command', { action, payload, id });
      } catch (err) {
        cleanup();
        console.error(`[TauriTransport] ❌ Erro ao invocar comando '${action}':`, err);
        reject(err);
      }
    });
  }

  async listen<TEvent = any>(event: string, callback: (data: TEvent) => void): Promise<UnlistenFn> {
    const { listen } = await import('@tauri-apps/api/event');
    return await listen<TEvent>(event, (evt) => {
      callback(evt.payload);
    });
  }
}
