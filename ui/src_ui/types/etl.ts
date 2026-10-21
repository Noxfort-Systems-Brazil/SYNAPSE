// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

export interface ParquetInspectionResult {
  num_rows: number;
  columns: string[];
  head: Record<string, any>[];
  size_mb: number;
}

export interface ParquetImportProgress {
  progress: number;
  status: string;
  isImporting: boolean;
}
