// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { ITransportClient, getTransportClient } from '../transport';
import { DataSourceItem, BatchPreviewResult, BatchImportResult } from '../../types/sensors';

export interface RegisterSourcePayload {
  id: string;
  name: string;
  is_local: boolean;
  connection?: string;
  source_type?: string;
  location?: string;
  associated_element?: string;
}

export interface UpdateSourcePayload {
  id: string;
  name?: string;
  is_local?: boolean;
  connection?: string;
  source_type?: string;
  location?: string;
  associated_element?: string;
}

export class SensorService {
  constructor(private transport: ITransportClient = getTransportClient()) {}

  async getSources(): Promise<DataSourceItem[]> {
    const res: any = await this.transport.invoke('get_sources');
    if (Array.isArray(res)) return res;
    if (res && Array.isArray(res.sources)) return res.sources;
    return [];
  }

  async addSource(payload: RegisterSourcePayload): Promise<{ success: boolean; message?: string }> {
    return await this.transport.invoke('add_source', payload);
  }

  async updateSource(payload: UpdateSourcePayload): Promise<{ success: boolean; message?: string }> {
    return await this.transport.invoke('update_source', payload);
  }

  async removeSource(sourceId: string): Promise<{ success: boolean }> {
    return await this.transport.invoke('remove_source', { source_id: sourceId });
  }

  async toggleOrigin(sourceId: string): Promise<{ success: boolean }> {
    return await this.transport.invoke('toggle_origin', { source_id: sourceId });
  }

  async associateSource(sourceId: string, elementId: string): Promise<{ success: boolean }> {
    return await this.transport.invoke('associate_source', { source_id: sourceId, element_id: elementId });
  }

  async previewBatchSources(csvContent?: string, filePath?: string): Promise<BatchPreviewResult> {
    return await this.transport.invoke('preview_batch_sources', {
      csv_content: csvContent,
      file_path: filePath,
    });
  }

  async importBatchSources(
    csvContent?: string,
    host?: string,
    port?: number,
    filePath?: string
  ): Promise<BatchImportResult> {
    return await this.transport.invoke('import_batch_sources', {
      csv_content: csvContent,
      file_path: filePath,
      host,
      port,
    });
  }
}

export const sensorService = new SensorService();
