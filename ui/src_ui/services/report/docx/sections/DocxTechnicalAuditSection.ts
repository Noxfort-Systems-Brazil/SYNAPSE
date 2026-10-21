// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { Paragraph, TextRun, Table, TableRow, AlignmentType } from 'docx';
import { OfficialReportData } from '../../../../types/report';
import {
  DocxTypographyConfig,
  ABNT_TABLE_BORDERS,
  createSectionHeading,
  createSubSectionHeading,
  createParagraphWithBoldLead,
  createTableCaption,
  createCarinaTableCell,
} from '../abntDocxStyles';

/**
 * Builds Part II: Technical Audit, HCM macroscopic overview, and metrological sensors inventory.
 */
export class DocxTechnicalAuditSection {
  public static build(
    report: OfficialReportData,
    config: DocxTypographyConfig
  ): (Paragraph | Table)[] {
    return [
      createSectionHeading('3. RELATÓRIO TÉCNICO E AUDITORIA DA MALHA SEMAFÓRICA', config),

      createSubSectionHeading('Preâmbulo e Objeto da Auditoria Técnica:', config),
      createParagraphWithBoldLead('Objeto da Auditoria:', report.auditObjective, config),
      createParagraphWithBoldLead('Diagnóstico Operacional do Tráfego:', report.observedTrafficDiagnosis, config),
      createParagraphWithBoldLead('Ação Semafórica Executada:', report.adaptiveActionExecuted, config),
      createParagraphWithBoldLead('Caracterização do Local:', `${report.location.corridorName} • ${report.location.centralNodes}.`, config),

      new Paragraph({ spacing: { before: 180 } }),

      createSubSectionHeading('Panorama Macroscópico da Malha Arterial (HCM):', config),
      new Paragraph({
        alignment: config.alignment,
        spacing: { line: config.lineSpacing, after: 180 },
        indent: { firstLine: config.paragraphIndent },
        children: [
          new TextRun({
            text: `A malha arterial auditada compreende uma extensão de ${report.networkSummary.networkLengthKm} km distribuída em ${report.networkSummary.corridorsMonitored} corredores principais, totalizando 18 interseções semafóricas coordenadas. O volume horário global aferido atingiu ${report.networkSummary.totalHourlyFlow}, com velocidade média espacial de ${report.networkSummary.networkMeanSpeed} e grau médio de saturação de ${report.networkSummary.networkMeanSaturation}, caracterizando Nível de Serviço ${report.networkSummary.networkLevelOfService}.`,
            size: config.bodySize,
            font: config.font,
          }),
        ],
      }),

      createSubSectionHeading('Inventário Metrológico dos Detectores e Equipamentos de Campo:', config),
      ...createTableCaption(
        'Tabela 2 – Discriminação dos detectores veiculares, equipamentos e grandezas aferidas.',
        config,
        'Fonte: Prefeitura Municipal / Secretaria de Trânsito / Metrologia Legal INMETRO (2026).'
      ),
      this.createSensorsTable(report, config),
    ];
  }

  private static createSensorsTable(report: OfficialReportData, config: DocxTypographyConfig): Table {
    const header = new TableRow({
      tableHeader: true,
      children: [
        createCarinaTableCell('ID', 16, config, { bold: true, fill: 'F2F2F2', bottomDarkBorder: true }),
        createCarinaTableCell('Interseção / Local', 26, config, { bold: true, fill: 'F2F2F2', bottomDarkBorder: true }),
        createCarinaTableCell('Tecnologia', 18, config, { bold: true, fill: 'F2F2F2', bottomDarkBorder: true }),
        createCarinaTableCell('Velocidade', 11, config, { bold: true, alignment: AlignmentType.RIGHT, fill: 'F2F2F2', bottomDarkBorder: true }),
        createCarinaTableCell('Volume', 11, config, { bold: true, alignment: AlignmentType.RIGHT, fill: 'F2F2F2', bottomDarkBorder: true }),
        createCarinaTableCell('Sat. (x)', 8, config, { bold: true, alignment: AlignmentType.RIGHT, fill: 'F2F2F2', bottomDarkBorder: true }),
        createCarinaTableCell('Laudo INMETRO', 10, config, { bold: true, fill: 'F2F2F2', bottomDarkBorder: true }),
      ],
    });

    const rows = report.sensors.map(
      (s, idx) =>
        new TableRow({
          children: [
            createCarinaTableCell(s.id, 16, config, { bold: true, fill: idx % 2 === 1 ? 'F8FAFC' : 'FFFFFF' }),
            createCarinaTableCell(s.junction, 26, config, { fill: idx % 2 === 1 ? 'F8FAFC' : 'FFFFFF' }),
            createCarinaTableCell(s.equipmentType, 18, config, { fill: idx % 2 === 1 ? 'F8FAFC' : 'FFFFFF' }),
            createCarinaTableCell(s.measuredSpeed, 11, config, { bold: true, alignment: AlignmentType.RIGHT, fill: idx % 2 === 1 ? 'F8FAFC' : 'FFFFFF' }),
            createCarinaTableCell(s.measuredFlow, 11, config, { bold: true, alignment: AlignmentType.RIGHT, fill: idx % 2 === 1 ? 'F8FAFC' : 'FFFFFF' }),
            createCarinaTableCell(s.saturationDegree.split(' ')[0], 8, config, { bold: true, alignment: AlignmentType.RIGHT, fill: idx % 2 === 1 ? 'F8FAFC' : 'FFFFFF' }),
            createCarinaTableCell(s.inmetroReport, 10, config, { fill: idx % 2 === 1 ? 'F8FAFC' : 'FFFFFF' }),
          ],
        })
    );

    return new Table({
      width: { size: 100, type: 'pct' as any },
      borders: ABNT_TABLE_BORDERS.carinaGrid,
      rows: [header, ...rows],
    });
  }
}
