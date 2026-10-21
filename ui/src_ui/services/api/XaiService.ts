// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { ITransportClient, getTransportClient } from '../transport';
import { OfficialReportData } from '../../types/report';

export class XaiService {
  constructor(private transport: ITransportClient = getTransportClient()) {}

  async explainBuffer(): Promise<{ success: boolean; message?: string }> {
    return await this.transport.invoke('explain_buffer');
  }

  async explainGlobal(): Promise<{ success: boolean; message?: string }> {
    return await this.transport.invoke('explain_global');
  }

  async explainLocal(nodeId: string): Promise<{ success: boolean; message?: string }> {
    return await this.transport.invoke('explain_local', { node_id: nodeId });
  }

  async generateOfficialReport(params?: Record<string, any>): Promise<{
    success: boolean;
    ready?: boolean;
    status?: string;
    message?: string;
    report?: OfficialReportData;
    formatted_markdown?: string;
    preview_html?: string;
    error?: string;
  }> {
    return await this.transport.invoke('generate_official_report', params || {}, 120000);
  }

  async exportOfficialReportDocx(params: {
    output_path?: string;
    report?: OfficialReportData;
    municipal_config?: Record<string, any>;
    typography_options?: Record<string, any>;
  }): Promise<{
    success: boolean;
    ready?: boolean;
    output_path?: string;
    protocol?: string;
    error?: string;
  }> {
    return await this.transport.invoke('export_official_report_docx', params);
  }
}

export const xaiService = new XaiService();
