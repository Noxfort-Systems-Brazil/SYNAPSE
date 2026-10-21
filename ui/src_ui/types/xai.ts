// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

export interface XaiAuditVerdict {
  safe: boolean;
  error: number;
  threshold: number;
  vector: number[];
  timestamp: string;
}

export interface LinguistClassification {
  source: string;
  type: string;
  confidence: number;
  timestamp: string;
}

export type XaiResultType = 'AUDITOR' | 'GLOBAL' | 'LOCAL';

export interface XaiResultItem {
  id: string;
  request_id?: string;
  type: XaiResultType;
  target: string;
  convergence_delta: number;
  semantic_text: string;
  attributions: number[];
  feature_names?: string[];
  timestamp: string;
}

export type XaiExplainMode = 'buffer' | 'global' | 'local';
