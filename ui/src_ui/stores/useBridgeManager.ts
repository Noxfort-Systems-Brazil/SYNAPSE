// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { UnlistenFn } from '../services/transport';
import { SynapseBridge } from '../services/bridge';

/**
 * Backward-Compatibility Facade (SOLID: DIP / Facade Pattern).
 * Preserves the public API contract for existing components (AppLayout, useSynapseStore)
 * while delegating all lifecycle, health watching, state hydration, and domain event routing
 * to decoupled, testable SOLID services in `services/bridge/`.
 */
export async function initSynapseBridge(): Promise<UnlistenFn> {
  const bridge = SynapseBridge.createDefault();
  return await bridge.initialize();
}

// Re-export bridge architecture for consumers
export * from '../services/bridge';
