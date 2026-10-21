// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

export type SystemPhase = 
  | 'IDLE_OPTIMIZATION'
  | 'RUNNING_OPTIMIZATION'
  | 'IDLE_OFFLINE'
  | 'RUNNING_OFFLINE'
  | 'IDLE_ONLINE'
  | 'RUNNING_ONLINE';

export type LogLevel = 'INFO' | 'WARN' | 'ERROR' | 'SYSTEM';

export interface LogEntry {
  id: string;
  timestamp: string;
  level: LogLevel;
  message: string;
}

export interface DatabaseConfig {
  host: string;
  port: number;
  dbname: string;
  schema?: string;
  user: string;
  password: string;
}

export interface DatabaseStatus {
  connected: boolean;
  message: string;
  checking: boolean;
}

export interface MonitorConfig {
  ip: string;
  host?: string;
  port?: number;
  connected?: boolean;
}

export interface MonitorStatus {
  connected: boolean;
  ip: string;
  host: string;
  port: number;
  message?: string;
}
