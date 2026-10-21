// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { BatchExportItem } from '../types/sensors';

export const SAMPLE_SENSOR_MANIFEST_CSV = `name,location
Camera 01 - Av Paulista Sentido Centro,cluster_12048
Camera 02 - Av Paulista Sentido Bairro,cluster_12048
Radar Tunel Reboucas Faixa 1,-edge_4401
Radar Tunel Reboucas Faixa 2,-edge_4401
`;

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
 * Serializes batch-imported sensor records into standard RFC 4180 CSV format.
 */
export function formatCameraConfigCsv(items: BatchExportItem[]): string {
  const header = 'id,name,location,resolved_type,push_url\n';
  const rows = items.map(
    (item) =>
      `"${item.id.replace(/"/g, '""')}","${item.name.replace(/"/g, '""')}","${item.location.replace(
        /"/g,
        '""'
      )}","${item.resolved_type}","${item.push_url}"`
  );
  return header + rows.join('\n') + '\n';
}
