// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { ITransportClient, getTransportClient } from '../transport';

export interface DuckDnsConfig {
  status: 'ONLINE' | 'DISCONNECTED';
  enabled: boolean;
  domain: string;
  token: string;
  caddy_enabled: boolean;
  port: number;
  https_port: number;
  public_url: string;
  caddy_running: boolean;
}

export interface DuckDnsTestResult {
  status: 'ok' | 'error';
  message?: string;
  error?: string;
  domain?: string;
  latency_ms?: number;
}

export class DuckDnsService {
  constructor(private transport: ITransportClient = getTransportClient()) {}

  async getConfig(): Promise<DuckDnsConfig> {
    return await this.transport.invoke('get_duckdns_config');
  }

  async saveConfig(config: Partial<DuckDnsConfig>): Promise<{
    status: string;
    message: string;
    public_url: string;
    online: boolean;
  }> {
    return await this.transport.invoke('save_duckdns_config', config);
  }

  async testConnection(domain: string, token: string): Promise<DuckDnsTestResult> {
    return await this.transport.invoke('test_duckdns_connection', { domain, token });
  }

  async toggleService(): Promise<{
    status: string;
    enabled: boolean;
    service_status: string;
    public_url: string;
  }> {
    return await this.transport.invoke('toggle_duckdns');
  }
}

export const duckDnsService = new DuckDnsService();
