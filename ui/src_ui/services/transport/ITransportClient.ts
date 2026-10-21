// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

export type UnlistenFn = () => void;

export interface ITransportClient {
  /**
   * Invoke a command on the backend core process (IPC / REST / WebSocket).
   */
  invoke<TPayload = any, TResponse = any>(
    action: string,
    payload?: TPayload,
    timeoutMs?: number
  ): Promise<TResponse>;

  /**
   * Listen to an asynchronous event stream emitted by the backend.
   */
  listen<TEvent = any>(event: string, callback: (data: TEvent) => void): Promise<UnlistenFn>;

  /**
   * Returns true if the client is connected to a native runtime (e.g., Tauri).
   */
  isNativeEnvironment(): boolean;
}
