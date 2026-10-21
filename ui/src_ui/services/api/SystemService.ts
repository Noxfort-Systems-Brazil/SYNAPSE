// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { ITransportClient, getTransportClient } from '../transport';
import { DatabaseConfig } from '../../types/system';
import { ParquetInspectionResult } from '../../types/etl';

export class SystemService {
  constructor(private transport: ITransportClient = getTransportClient()) {}

  async getSystemStatus(): Promise<any> {
    return await this.transport.invoke('get_system_status');
  }

  async startOptimization(): Promise<any> {
    return await this.transport.invoke('start_optimization');
  }

  async stopOptimization(): Promise<any> {
    return await this.transport.invoke('stop_optimization');
  }

  async startOfflineBootstrap(): Promise<any> {
    return await this.transport.invoke('start_offline_bootstrap');
  }

  async stopOfflineBootstrap(): Promise<any> {
    return await this.transport.invoke('stop_offline_bootstrap');
  }

  async startOnlineOperation(): Promise<any> {
    return await this.transport.invoke('start_online_operation');
  }

  async stopOnlineOperation(): Promise<any> {
    return await this.transport.invoke('stop_online_operation');
  }

  async resetWorkspace(): Promise<{ success: boolean; message: string }> {
    return await this.transport.invoke('reset_workspace');
  }

  async testDbConnection(config: DatabaseConfig): Promise<{ success: boolean; message: string }> {
    return await this.transport.invoke('test_db_connection', { config });
  }

  async initializeDb(rootPassword: string, config: DatabaseConfig): Promise<{ success: boolean; message: string }> {
    return await this.transport.invoke('initialize_db', { root_password: rootPassword, config });
  }

  async getDatabaseConfig(): Promise<any> {
    return await this.transport.invoke('get_database_config');
  }

  async disconnectDb(): Promise<any> {
    return await this.transport.invoke('disconnect_db');
  }

  async getTelemetryConfig(): Promise<any> {
    return await this.transport.invoke('get_telemetry_config');
  }

  async saveTelemetryConfig(config: { ip: string; host?: string; port?: number; connected: boolean }): Promise<any> {
    return await this.transport.invoke('save_telemetry_config', config);
  }

  async testTelemetryConnection(config: { ip: string; host?: string; port?: number }): Promise<{ success: boolean; message: string }> {
    return await this.transport.invoke('test_telemetry_connection', config);
  }

  async inspectParquet(path: string): Promise<ParquetInspectionResult> {
    return await this.transport.invoke('inspect_parquet', { path });
  }

  async importParquet(path: string): Promise<{ success: boolean; message?: string }> {
    return await this.transport.invoke('import_parquet', { path });
  }

  async getNetworkInfo(): Promise<{ local_ip: string }> {
    return await this.transport.invoke('get_network_info');
  }

  private isFilePickerOpen = false;

  async pickFile(options?: {
    title?: string;
    filter?: string;
    filterName?: string;
    extensions?: string[];
  }): Promise<{ path: string | null; cancelled: boolean }> {
    if (this.isFilePickerOpen) {
      console.warn('[SystemService] Diálogo de seleção de arquivo já está em aberto; ignorando chamada duplicada.');
      return { path: null, cancelled: true };
    }

    this.isFilePickerOpen = true;

    try {
      let extensions = options?.extensions;
      let filterName = options?.filterName;

      if (options?.filter) {
        const parts = options.filter.split('|');
        if (!filterName) {
          filterName = parts[0]?.trim() || 'Arquivos';
        }
        if (!extensions && parts.length > 1) {
          extensions = parts[1]
            .trim()
            .split(/\s+/)
            .map((ext) => ext.replace(/^\*\./, '').replace(/^\./, ''))
            .filter(Boolean);
        }
      }

      try {
        const { invoke } = await import('@tauri-apps/api/core');
        const res = await invoke<string | null>('pick_file_dialog', {
          title: options?.title || 'Selecionar Arquivo',
          filterName: filterName || 'Arquivos',
          filterExtensions: extensions && extensions.length > 0 ? extensions : ['parquet'],
        });
        return { path: res, cancelled: res === null };
      } catch (err) {
        console.warn('[SystemService] Falha ao invocar Tauri pick_file_dialog, tentando IPC:', err);
        try {
          return await this.transport.invoke('pick_file', options || {});
        } catch (ipcErr) {
          console.warn('[SystemService] Falha ao invocar pick_file via IPC:', ipcErr);
          return { path: null, cancelled: true };
        }
      }
    } finally {
      this.isFilePickerOpen = false;
    }
  }

  async saveFile(options?: {
    defaultFilename?: string;
    title?: string;
    filter?: string;
    filterName?: string;
    extensions?: string[];
  }): Promise<{ path: string | null; cancelled: boolean }> {
    let extensions = options?.extensions;
    let filterName = options?.filterName;

    if (options?.filter) {
      const parts = options.filter.split('|');
      if (!filterName) {
        filterName = parts[0]?.trim() || 'Documentos Word';
      }
      if (!extensions && parts.length > 1) {
        extensions = parts[1]
          .trim()
          .split(/\s+/)
          .map((ext) => ext.replace(/^\*\./, '').replace(/^\./, ''))
          .filter(Boolean);
      }
    }

    try {
      const { invoke } = await import('@tauri-apps/api/core');
      const res = await invoke<string | null>('save_file_dialog', {
        defaultFilename: options?.defaultFilename,
        title: options?.title || 'Salvar Arquivo',
        filterName: filterName || 'Documentos Word (*.docx)',
        filterExtensions: extensions && extensions.length > 0 ? extensions : ['docx'],
      });
      return { path: res, cancelled: res === null };
    } catch (err) {
      console.warn('[SystemService] Falha ao invocar Tauri save_file_dialog, tentando IPC:', err);
      try {
        const res = await this.transport.invoke<any, { path?: string | null; cancelled?: boolean }>('save_file', {
          title: options?.title || 'Salvar Arquivo',
          default_filename: options?.defaultFilename,
          filter: options?.filter || (extensions ? extensions.map((e) => `*.${e}`).join(' ') : '*.docx'),
        });
        return { path: res?.path || null, cancelled: Boolean(res?.cancelled) };
      } catch (ipcErr) {
        console.warn('[SystemService] Falha ao invocar save_file via IPC:', ipcErr);
        return { path: null, cancelled: true };
      }
    }
  }

  async pickDirectory(options?: {
    title?: string;
  }): Promise<{ path: string | null; cancelled: boolean }> {
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      const res = await invoke<string | null>('pick_directory_dialog', {
        title: options?.title || 'Selecionar Pasta',
      });
      return { path: res, cancelled: res === null };
    } catch (err) {
      console.warn('[SystemService] Falha ao invocar Tauri pick_directory_dialog, tentando IPC:', err);
      try {
        const res = await this.transport.invoke<any, { path?: string | null; cancelled?: boolean }>('pick_directory', {
          title: options?.title || 'Selecionar Pasta',
        });
        return { path: res?.path || null, cancelled: Boolean(res?.cancelled) };
      } catch (ipcErr) {
        console.warn('[SystemService] Falha ao invocar pick_directory via IPC:', ipcErr);
        return { path: null, cancelled: true };
      }
    }
  }

}


export const systemService = new SystemService();
