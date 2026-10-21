// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import {
  IReportExportService,
  OfficialReportData,
  ReportTypographyOptions,
} from '../../types/report';
import { BrowserDownloadService } from './exporters/BrowserDownloadService';
import { DocxReportExporter } from './exporters/DocxReportExporter';
import { PdfReportExporter } from './exporters/PdfReportExporter';

/**
 * Single Responsibility: Facade for report exporting operations (SOLID: SRP & DIP).
 * Delegates concrete operations to specialized exporters:
 * - DocxReportExporter: Word .docx generation and platform saving
 * - PdfReportExporter: Multi-page ABNT PDF rendering and saving
 * - BrowserDownloadService: Clipboard, print, and browser anchor links
 */
export class BrowserReportExportService implements IReportExportService {
  public async copyToClipboard(text: string): Promise<boolean> {
    return BrowserDownloadService.copyToClipboard(text);
  }

  public print(): void {
    BrowserDownloadService.print();
  }

  public downloadMarkdown(filename: string, content: string): void {
    BrowserDownloadService.downloadMarkdown(filename, content);
  }

  public async exportToDocx(
    report: OfficialReportData,
    filename: string,
    options?: ReportTypographyOptions
  ): Promise<boolean> {
    return DocxReportExporter.export(report, filename, options);
  }

  public async exportToPdf(elementId: string, filename: string): Promise<boolean> {
    return PdfReportExporter.export(elementId, filename);
  }
}

export const defaultReportExportService = new BrowserReportExportService();
