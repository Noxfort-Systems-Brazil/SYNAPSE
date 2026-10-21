// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import { BrowserDownloadService } from './BrowserDownloadService';

export class PdfReportExporter {
  public static async export(elementId: string, filename: string): Promise<boolean> {
    try {
      const container = document.getElementById(elementId);
      if (!container) {
        BrowserDownloadService.print();
        return true;
      }

      const pageElements = Array.from(container.querySelectorAll<HTMLElement>('.abnt-a4-page'));

      const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4',
        compress: true,
      });

      if (pageElements.length > 0) {
        for (let i = 0; i < pageElements.length; i++) {
          const pageEl = pageElements[i];
          if (i > 0) {
            pdf.addPage();
          }

          const canvas = await html2canvas(pageEl, {
            scale: 2.5,
            useCORS: true,
            logging: false,
            backgroundColor: '#ffffff',
          });

          const imgData = canvas.toDataURL('image/jpeg', 0.95);
          pdf.addImage(imgData, 'JPEG', 0, 0, 210, 297, undefined, 'FAST');
        }
      } else {
        const canvas = await html2canvas(container, {
          scale: 2,
          useCORS: true,
          logging: false,
          backgroundColor: '#ffffff',
        });

        const imgData = canvas.toDataURL('image/png');
        const imgWidth = 210;
        const pageHeight = 297;
        const imgHeight = (canvas.height * imgWidth) / canvas.width;
        let heightLeft = imgHeight;
        let position = 0;

        pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight, undefined, 'FAST');
        heightLeft -= pageHeight;

        while (heightLeft > 0) {
          position = heightLeft - imgHeight;
          pdf.addPage();
          pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight, undefined, 'FAST');
          heightLeft -= pageHeight;
        }
      }

      const cleanFilename = filename.endsWith('.pdf') ? filename : `${filename}.pdf`;
      const base64DataUri = pdf.output('datauristring');
      const pdfBlob = pdf.output('blob');

      return await BrowserDownloadService.saveWithPlatformBridge(
        cleanFilename,
        'Salvar Laudo Técnico Operacional (PDF)',
        'Documento PDF (*.pdf)',
        ['pdf'],
        base64DataUri,
        pdfBlob,
        'application/pdf'
      );
    } catch (error) {
      console.error('[PdfReportExporter] Failed to export PDF:', error);
      return false;
    }
  }
}
