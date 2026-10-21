// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import {
  Paragraph,
  TextRun,
  Table,
  TableRow,
  TableCell,
  WidthType,
  AlignmentType,
} from 'docx';
import { OfficialReportData } from '../../../../types/report';
import {
  DocxTypographyConfig,
  ABNT_TABLE_BORDERS,
  createSectionHeading,
  createCarinaTableCell,
} from '../abntDocxStyles';

/**
 * Builds the official institutional header, date, title, and operational environment table
 * in identical conformity with the Carina benchmark (sas.docx / mfd.docx).
 */
export class DocxHeaderSection {
  public static build(report: OfficialReportData, config: DocxTypographyConfig): (Paragraph | Table)[] {
    const formattedDate = new Date(report.timestamp).toLocaleDateString('pt-BR', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    });

    return [
      // 1. Table 1 Institutional Header (Municipal Letterhead)
      this.createInstitutionalHeaderTable(report, config),

      // Blank separator line
      new Paragraph({ spacing: { before: 120, after: 120 } }),

      // Date and Location Right-Aligned
      new Paragraph({
        alignment: AlignmentType.RIGHT,
        spacing: { after: 140 },
        children: [
          new TextRun({
            text: `São Paulo - SP, ${formattedDate}`,
            size: config.noteSize,
            font: config.font,
            color: '000000',
          }),
        ],
      }),

      // Report Title
      new Paragraph({
        alignment: AlignmentType.LEFT,
        spacing: { after: 80 },
        children: [
          new TextRun({
            text: `LAUDO TÉCNICO OPERACIONAL DE ENGENHARIA DE TRÁFEGO Nº ${report.protocol}`,
            bold: true,
            size: config.titleSize,
            font: config.font,
            color: '000000',
          }),
        ],
      }),

      // Assunto
      new Paragraph({
        alignment: AlignmentType.LEFT,
        spacing: { after: 240 },
        children: [
          new TextRun({
            text: 'Assunto: ',
            bold: true,
            size: config.noteSize,
            font: config.font,
            color: '000000',
          }),
          new TextRun({
            text: 'Análise da Capacidade Operacional, Conformidade com as Resoluções do CONTRAN e Auditoria da Programação Semafórica Adaptativa da Malha Arterial.',
            size: config.noteSize,
            font: config.font,
            color: '3C3C3C',
          }),
        ],
      }),

      // 2. Section 1: IDENTIFICATION AND OPERATIONAL ENVIRONMENT
      createSectionHeading('1. IDENTIFICAÇÃO E AMBIENTE OPERACIONAL', config),
      this.createOperationalEnvironmentTable(report, config),
    ];
  }

  private static createInstitutionalHeaderTable(
    report: OfficialReportData,
    config: DocxTypographyConfig
  ): Table {
    return new Table({
      width: { size: 100, type: WidthType.PERCENTAGE },
      borders: ABNT_TABLE_BORDERS.frameless,
      rows: [
        new TableRow({
          children: [
            new TableCell({
              width: { size: 18, type: WidthType.PERCENTAGE },
              children: [
                new Paragraph({
                  alignment: AlignmentType.CENTER,
                  spacing: { before: 40, after: 40 },
                  children: [
                    new TextRun({
                      text: 'BRASÃO OFICIAL',
                      bold: true,
                      size: config.microSize,
                      font: config.font,
                      color: '505050',
                    }),
                  ],
                }),
              ],
            }),

            new TableCell({
              width: { size: 82, type: WidthType.PERCENTAGE },
              children: [
                new Paragraph({
                  alignment: AlignmentType.LEFT,
                  spacing: { after: 40 },
                  children: [
                    new TextRun({
                      text: report.cityHall.toUpperCase(),
                      bold: true,
                      size: config.bodySize,
                      font: config.font,
                      color: '000000',
                    }),
                  ],
                }),
                new Paragraph({
                  alignment: AlignmentType.LEFT,
                  spacing: { after: 20 },
                  children: [
                    new TextRun({
                      text: report.department,
                      size: config.noteSize,
                      font: config.font,
                      color: '3C3C3C',
                    }),
                  ],
                }),
                new Paragraph({
                  alignment: AlignmentType.LEFT,
                  children: [
                    new TextRun({
                      text: 'Supervisão de Engenharia de Tráfego e Controle Semafórico em Tempo Real',
                      italics: true,
                      size: config.smallSize,
                      font: config.font,
                      color: '505050',
                    }),
                  ],
                }),
              ],
            }),
          ],
        }),
      ],
    });
  }

  private static createOperationalEnvironmentTable(
    report: OfficialReportData,
    config: DocxTypographyConfig
  ): Table {
    const row = (label: string, value: string, isAlternate: boolean = false) =>
      new TableRow({
        children: [
          createCarinaTableCell(label, 40, config, {
            bold: true,
            fill: isAlternate ? 'F8FAFC' : 'FFFFFF',
          }),
          createCarinaTableCell(value, 60, config, {
            fill: isAlternate ? 'F8FAFC' : 'FFFFFF',
          }),
        ],
      });

    return new Table({
      width: { size: 100, type: WidthType.PERCENTAGE },
      borders: ABNT_TABLE_BORDERS.carinaGrid,
      rows: [
        row('Identificador do Agente / Sistema:', 'SYNAPSE v2.0 Enterprise', false),
        row('Cenário de Operação:', 'Sessão de Operação e Supervisão em Tempo Real (CCO)', true),
        row('Motor Analítico de Percepção:', 'SYNAPSE Adaptive Traffic Perception Engine', false),
        row('Processo Administrativo:', report.processNumber, true),
        row('Autoridade de Trânsito Responsável:', `${report.authorityName} (${report.authorityRole})`, false),
        row('Identificação Funcional / Portaria:', report.registrationNumber, true),
        row('Corredor Viário Fiscalizado:', report.location.corridorName, false),
        row('Data e Horário da Auditoria:', new Date(report.timestamp).toLocaleString('pt-BR'), true),
      ],
    });
  }
}
