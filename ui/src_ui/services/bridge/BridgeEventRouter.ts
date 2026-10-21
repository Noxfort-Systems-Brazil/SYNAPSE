// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { ITransportClient, UnlistenFn } from '../transport';
import { IBridgeEventHandler, IBridgeEventRouter } from './types';

/**
 * Open/Closed Principle (OCP) & Single Responsibility Principle (SRP):
 * Dynamically binds registered event handlers to the underlying transport listener stream.
 * New event domains can be added without modifying this router.
 */
export class BridgeEventRouter implements IBridgeEventRouter {
  private readonly handlers: IBridgeEventHandler[] = [];

  constructor(private readonly transport: ITransportClient) {}

  registerHandler(handler: IBridgeEventHandler): void {
    this.handlers.push(handler);
  }

  async start(): Promise<UnlistenFn> {
    const unlisteners: UnlistenFn[] = [];

    for (const handler of this.handlers) {
      for (const event of handler.events) {
        try {
          const unlisten = await this.transport.listen(event, async (data: any) => {
            try {
              await handler.handle(event, data);
            } catch (err) {
              console.error(`[BridgeEventRouter] Error handling event '${event}':`, err);
            }
          });
          unlisteners.push(unlisten);
        } catch (err) {
          console.error(`[BridgeEventRouter] Failed to attach listener for event '${event}':`, err);
        }
      }
    }

    return () => {
      unlisteners.forEach((unlisten) => {
        try {
          unlisten();
        } catch (err) {
          console.error('[BridgeEventRouter] Error executing unlistener:', err);
        }
      });
    };
  }
}
