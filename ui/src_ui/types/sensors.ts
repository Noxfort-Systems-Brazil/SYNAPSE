// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

export type SourceStatusType = 
  | 'Active' 
  | 'Quarantine' 
  | 'Validating' 
  | 'Rejected' 
  | 'Fallback' 
  | 'Offline';

export interface BaseDataSource {
  id: string;
  name: string;
  status: SourceStatusType;
  quality?: number;
  semantic_type?: string;
  confidence_score?: number;
  latest_value?: number | string | null;
  quarantine_count?: number;
  associated_element?: string;
  associated_element_name?: string | null;
  source_type?: string;
  connection_string?: string;
}

export interface LocalSensorSource extends BaseDataSource {
  is_local: true;
  lat?: number;
  lon?: number;
}

export interface GlobalApiSource extends BaseDataSource {
  is_local: false;
  endpoint_url?: string;
}

export type DataSourceItem = LocalSensorSource | GlobalApiSource;

export interface TelemetryPoint {
  time: string;
  value: number;
}

export interface EngineDataPayload {
  timestamp?: number;
  cycle?: number;
  active_sensors_count?: number;
  mean_speed?: number;
  mean_occupancy?: number;
  loss?: number;
  losses?: Record<string, number>;
  drift?: number;
  drift_scores?: Record<string, number>;
  qualities?: Record<string, number>;
  edge_data?: Record<string, { speed: number; occupancy: number; density?: number; queue?: number }>;
  sensor_snapshot?: Record<string, any>;
  source_values?: Record<string, number>;
}

export interface BatchPreviewItem {
  line: number;
  name: string;
  type: 'local' | 'global';
  id: string;
  address: string;
  location?: string;
  resolved_type: 'NODE' | 'EDGE' | 'GLOBAL_API' | 'UNKNOWN' | 'INVALID';
  error?: string | null;
}

export interface BatchPreviewResult {
  total: number;
  valid_count: number;
  error_count: number;
  parse_errors?: string[];
  items: BatchPreviewItem[];
}

export interface BatchExportItem {
  id: string;
  name: string;
  type: 'local' | 'global';
  location: string;
  address: string;
  resolved_type: string;
  push_url: string;
}

export interface BatchImportResult {
  success: boolean;
  message?: string;
  imported_count: number;
  items: BatchExportItem[];
  errors?: string[];
}

