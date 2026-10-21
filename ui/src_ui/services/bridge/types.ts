// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { UnlistenFn } from '../transport';

export type LogLevel = 'INFO' | 'WARN' | 'ERROR' | 'SYSTEM';

/**
 * Interface Segregation (ISP): Sink for connection state, latency, and log outputs.
 */
export interface IConnectionSink {
  setConnected(connected: boolean): void;
  setLatencyMs(latency: number): void;
  addLog(level: LogLevel, message: string): void;
  isConnected(): boolean;
}

/**
 * Interface Segregation (ISP): Sink for hydrating initial state from disk into stores.
 */
export interface IStateHydratorSink {
  setPhase(phase: string): void;
  setTopology(nodes: any[], edges: any[]): void;
  setSources(sources: any[]): void;
  setDbStatus(status: { connected: boolean; message: string }): void;
  setMonitorStatus(status: { connected: boolean; ip: string; host: string; port: number; message: string }): void;
  setHasDataset?(has: boolean): void;
  addLog(level: LogLevel, message: string): void;
}

/**
 * Open/Closed Principle (OCP): Handler interface for processing specific incoming IPC events.
 */
export interface IBridgeEventHandler {
  readonly events: readonly string[];
  handle(event: string, payload: any): void | Promise<void>;
}

/**
 * Single Responsibility Principle (SRP): Monitors connection ping, RTT latency, and background heartbeats.
 */
export interface IConnectionHealthWatcher {
  start(onConnected?: () => Promise<void> | void): void;
  dispose(): void;
}

/**
 * Single Responsibility Principle (SRP): Hydrates application state from persistent backend files.
 */
export interface IStateHydrator {
  hydrate(): Promise<void>;
}

/**
 * Single Responsibility Principle (SRP): Routes IPC events to registered domain handlers.
 */
export interface IBridgeEventRouter {
  registerHandler(handler: IBridgeEventHandler): void;
  start(): Promise<UnlistenFn>;
}

/**
 * Central orchestrator interface for the Synapse IPC Bridge.
 */
export interface ISynapseBridge {
  initialize(): Promise<UnlistenFn>;
  dispose(): void;
}
