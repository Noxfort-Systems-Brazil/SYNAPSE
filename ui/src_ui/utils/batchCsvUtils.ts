// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { BatchExportItem, DataSourceItem } from '../types/sensors';

import { BrowserDownloadService } from '../services/report/exporters/BrowserDownloadService';
import { systemService } from '../services/api';

export const SAMPLE_SENSOR_MANIFEST_CSV = `name,type,id,address
Camera 01 - Av Paulista Sentido Centro,local,cluster_12048,192.168.1.101
Camera 02 - Av Paulista Sentido Bairro,local,cluster_12048,192.168.1.102
Radar Tunel Reboucas Faixa 1,local,-edge_4401,
Radar Tunel Reboucas Faixa 2,local,-edge_4401,
Feed Trafego Waze SP,global,,https://api.waze.com/traffic/sp
Servico Clima e Chuva,global,,http://10.0.0.50:8080/weather
`;

/**
 * Triggers a file download using Tauri native save dialog when on desktop,
 * or standard browser download when in web environment (SOLID: DIP).
 */
export async function downloadCsvWithPlatformBridge(
  filename: string,
  content: string,
  title: string = 'Salvar Arquivo CSV'
): Promise<boolean> {
  const bytes = new TextEncoder().encode(content);
  let binary = '';
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  const base64 = window.btoa(binary);
  const base64DataUri = `data:text/csv;charset=utf-8;base64,${base64}`;
  const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });

  return await BrowserDownloadService.saveWithPlatformBridge(
    filename,
    title,
    'Arquivo CSV (*.csv)',
    ['csv'],
    base64DataUri,
    blob,
    'text/csv'
  );
}

/**
 * Triggers a browser file download from an in-memory string.
 */
export function triggerBlobDownload(
  filename: string,
  content: string,
  mimeType: string = 'text/csv;charset=utf-8;'
): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Serializes batch-imported local sensor records into simplified RFC 4180 CSV format (name,address).
 * Exclusively exports local sensors, where 'address' is the Synapse push URL generated for ingest.
 */
export function formatCameraConfigCsv(items: BatchExportItem[]): string {
  const localItems = items.filter((item) => item.type === 'local');
  const header = 'name,address\n';
  const rows = localItems.map(
    (item) =>
      `"${item.name.replace(/"/g, '""')}","${item.push_url.replace(/"/g, '""')}"`
  );
  return header + rows.join('\n') + '\n';
}

/**
 * Serializes registered DataSourceItem records into simplified RFC 4180 CSV format (name,address).
 * Exclusively exports local sensors, where 'address' is the Synapse push URL configured or generated for ingest.
 */
export function formatLocalSensorsCsv(
  sources: DataSourceItem[],
  fallbackBaseEndpoint?: string
): string {
  const localItems = sources.filter(
    (s) =>
      s.is_local &&
      s.source_type !== 'SUMO Network' &&
      s.id !== 'map_main' &&
      s.source_type !== 'Parquet' &&
      s.id !== 'historical_base'
  );

  const header = 'name,address\n';
  const rows = localItems.map((item) => {
    let address = item.connection_string || '';
    if (!address && fallbackBaseEndpoint) {
      const cleanBase = fallbackBaseEndpoint.replace(/\/+$/, '');
      address = `${cleanBase}/${item.id}`;
    }
    return `"${item.name.replace(/"/g, '""')}","${address.replace(/"/g, '""')}"`;
  });

  return header + rows.join('\n') + '\n';
}

/**
 * Downloads local registered sensors config CSV using the platform bridge (Tauri native / Web).
 */
export async function exportLocalSensorsCsv(
  sources: DataSourceItem[]
): Promise<boolean> {
  const localItems = sources.filter(
    (s) =>
      s.is_local &&
      s.source_type !== 'SUMO Network' &&
      s.id !== 'map_main' &&
      s.source_type !== 'Parquet' &&
      s.id !== 'historical_base'
  );

  if (localItems.length === 0) {
    return false;
  }

  // Check if any local item lacks an explicit connection_string
  const needsFallback = localItems.some((item) => !item.connection_string);
  let baseEndpoint = '';
  if (needsFallback) {
    try {
      const netInfo: any = await systemService.getNetworkInfo();
      baseEndpoint =
        netInfo?.unified_endpoint ||
        (netInfo?.local_ip
          ? `http://${netInfo.local_ip}:${netInfo.gateway_port || 8081}`
          : 'http://127.0.0.1:8081');
    } catch {
      baseEndpoint = 'http://127.0.0.1:8081';
    }
  }

  const csvContent = formatLocalSensorsCsv(sources, baseEndpoint);
  return await downloadCsvWithPlatformBridge(
    'config_cameras_locais.csv',
    csvContent,
    'Salvar Configuração das Câmeras Locais'
  );
}
