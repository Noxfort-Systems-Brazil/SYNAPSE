// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { OfficialReportData, ReportTypographyOptions } from '../../../types/report';
import { DocxReportBuilder } from '../docxReportBuilder';
import { BrowserDownloadService } from './BrowserDownloadService';

export class DocxReportExporter {
  public static async export(
    report: OfficialReportData,
    filename: string,
    options?: ReportTypographyOptions
  ): Promise<boolean> {
    try {
      const docxBlob = await DocxReportBuilder.generateBlob(report, options);
      const cleanFilename = filename.endsWith('.docx') ? filename : `${filename}.docx`;

      // Convert blob to base64 Data URI for Tauri bridge
      const base64DataUri = await new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => {
          if (typeof reader.result === 'string') {
            resolve(reader.result);
          } else {
            reject(new Error('Failed to convert docx blob to base64'));
          }
        };
        reader.onerror = reject;
        reader.readAsDataURL(docxBlob);
      });

      return await BrowserDownloadService.saveWithPlatformBridge(
        cleanFilename,
        'Salvar Laudo Técnico Oficial (.docx)',
        'Documento do Microsoft Word (*.docx)',
        ['docx'],
        base64DataUri,
        docxBlob,
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
      );
    } catch (error) {
      console.error('[DocxReportExporter] Failed to export DOCX:', error);
      return false;
    }
  }
}
