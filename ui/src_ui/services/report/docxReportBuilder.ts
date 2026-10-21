// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import {
  Document,
  Packer,
  Paragraph,
  TextRun,
  Header,
  Footer,
  PageNumber,
  PageBreak,
  AlignmentType,
} from 'docx';
import { OfficialReportData, ReportTypographyOptions } from '../../types/report';
import { getDocxTypographyConfig, DocxTypographyConfig } from './docx/abntDocxStyles';
import {
  DocxHeaderSection,
  DocxExecutiveSummarySection,
  DocxTechnicalAuditSection,
  DocxSafetyAttributionSection,
  DocxMathFormulasSection,
  DocxQuesitosLegalSection,
  DocxClosingSection,
} from './docx/sections';

/**
 * Single Responsibility: Orchestrates high-level ABNT document assembly and compiles OpenXML Blob.
 * Section formatting and domain-specific rules are decoupled into dedicated SOLID builders.
 */
export class DocxReportBuilder {
  public static async generateBlob(
    report: OfficialReportData,
    options?: ReportTypographyOptions
  ): Promise<Blob> {
    const config = getDocxTypographyConfig(options);

    const doc = new Document({
      creator: 'SYNAPSE v2.0 Enterprise',
      title: `Relatório Técnico de Tráfego - ${report.protocol}`,
      description: 'Laudo Técnico e Relatório de Auditoria de Tráfego conforme normas da ABNT e CTB Art. 24',
      sections: [
        {
          properties: {
            page: {
              margin: config.margins,
            },
          },
          headers: {
            default: this.createDocumentHeader(report, config),
          },
          footers: {
            default: this.createDocumentFooter(config),
          },
          children: [
            // 1. Institutional Letterhead, Title, and Case Docketing
            ...DocxHeaderSection.build(report, config),

            new Paragraph({ spacing: { before: 240 } }),

            // 2. PART I — Executive Summary for Public Management and Performance Table
            ...DocxExecutiveSummarySection.build(report, config),

            // Formal Page Break for Part II
            new Paragraph({ children: [new PageBreak()] }),

            // 3. PART II — Technical Report, HCM Overview, and Sensor Detector Table
            ...DocxTechnicalAuditSection.build(report, config),

            new Paragraph({ spacing: { before: 180 } }),

            // 4. CONTRAN Safety Audit and Causal Traffic Attribution
            ...DocxSafetyAttributionSection.build(report, config),

            // Page Break for Mathematical Formulations and Legal Quesitos
            new Paragraph({ children: [new PageBreak()] }),

            // 5. Mathematical Calculation Memorial (Formulas 1 to 6) and Counterfactual
            ...DocxMathFormulasSection.build(report, config),

            new Paragraph({ spacing: { before: 180 } }),

            // 6. Response to Technical Quesitos and Regulatory Framework
            ...DocxQuesitosLegalSection.build(report, config),

            new Paragraph({ spacing: { before: 240 } }),

            // 7. Conclusive Technical Opinion, Signature Block, and ABNT References
            ...DocxClosingSection.build(report, config),
          ],
        },
      ],
    });

    return await Packer.toBlob(doc);
  }

  private static createDocumentHeader(
    report: OfficialReportData,
    config: DocxTypographyConfig
  ): Header {
    return new Header({
      children: [
        new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [
            new TextRun({
              text: `${report.cityHall} • ${report.department} • Processo: ${report.processNumber}`,
              size: config.microSize,
              font: config.font,
              color: '555555',
            }),
          ],
        }),
      ],
    });
  }

  private static createDocumentFooter(config: DocxTypographyConfig): Footer {
    return new Footer({
      children: [
        new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [
            new TextRun({
              text: 'SYNAPSE Percepção de Tráfego • Folha ',
              size: config.microSize,
              font: config.font,
              color: '555555',
            }),
            new TextRun({
              children: [PageNumber.CURRENT],
              size: config.microSize,
              font: config.font,
              color: '555555',
            }),
            new TextRun({
              text: ' de ',
              size: config.microSize,
              font: config.font,
              color: '555555',
            }),
            new TextRun({
              children: [PageNumber.TOTAL_PAGES],
              size: config.microSize,
              font: config.font,
              color: '555555',
            }),
          ],
        }),
      ],
    });
  }
}
