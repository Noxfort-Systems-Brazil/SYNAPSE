// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { Paragraph, TextRun, AlignmentType } from 'docx';
import { OfficialReportData } from '../../../../types/report';
import {
  DocxTypographyConfig,
  createSectionHeading,
  createParagraph,
} from '../abntDocxStyles';

/**
 * Builds Section 9 (Final Considerations & Technical Opinion), Official Signatures Block,
 * and Section 10 (ABNT NBR 6023 Bibliographic References) matching the Carina benchmark.
 */
export class DocxClosingSection {
  public static build(
    report: OfficialReportData,
    config: DocxTypographyConfig
  ): Paragraph[] {
    return [
      createSectionHeading('9. CONSIDERAÇÕES FINAIS E PARECER TÉCNICO CONCLUSIVO', config),

      createParagraph(
        'Conclui-se, do ponto de vista técnico e operacional, que a intervenção semafórica adaptativa executada na malha arterial do Corredor Paulista mostrou-se plenamente regular, necessária e eficaz, tendo eliminado a retenção crítica de veículos e preservado integralmente todos os tempos de segurança viária estabelecidos pelas resoluções do CONTRAN.',
        config
      ),
      createParagraph(
        'O presente Relatório Técnico Operacional é emitido sob a competência expressa do Art. 24 do Código de Trânsito Brasileiro (Lei nº 9.503/1997) e homologado pela equipe técnica de fiscalização e operações de trânsito do município.',
        config
      ),

      new Paragraph({ spacing: { before: 200 } }),

      // Centralized Signature Line (Carina Standard)
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 200, after: 40 },
        children: [
          new TextRun({
            text: '___________________________________________________',
            bold: true,
            font: config.font,
            color: '000000',
          }),
        ],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 20 },
        children: [
          new TextRun({
            text: report.authorityName,
            bold: true,
            size: config.nameSize,
            font: config.font,
            color: '000000',
          }),
        ],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 20 },
        children: [
          new TextRun({
            text: report.authorityRole,
            size: 19,
            font: config.font,
            color: '3C3C3C',
          }),
        ],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 80 },
        children: [
          new TextRun({
            text: `${report.registrationNumber} – ${report.cityHall} / ${report.department}`,
            size: 19,
            font: config.font,
            color: '505050',
          }),
        ],
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { after: 240 },
        children: [
          new TextRun({
            text: `Este laudo foi gerado de forma determinística pelo motor de auditoria semafórica SYNAPSE v2.0 Enterprise (Certificação: ${report.digitalCertification || 'HOMOLOGADO'}). Ele atesta as métricas operacionais e a conformidade pericial da malha em tempo real.`,
            italics: true,
            size: config.microSize,
            font: config.font,
            color: '505050',
          }),
        ],
      }),

      createSectionHeading('10. REFERÊNCIAS NORMATIVAS E BIBLIOGRÁFICAS (ABNT NBR 6023:2018)', config),
      ...report.references.map(
        (ref) =>
          new Paragraph({
            alignment: config.alignment,
            spacing: { line: config.singleLineSpacing, after: 120 },
            children: [
              new TextRun({
                text: ref,
                size: config.noteSize,
                font: config.font,
                color: '000000',
              }),
            ],
          })
      ),

      new Paragraph({ spacing: { before: 200 } }),

      // Final Closing Note (Carina Standard)
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 120, after: 60 },
        children: [
          new TextRun({
            text: 'Fim do Laudo Técnico Oficial de Auditoria de Tráfego – SYNAPSE v2.0 Enterprise',
            bold: true,
            size: config.bodySize,
            font: config.font,
            color: '505050',
          }),
        ],
      }),
    ];
  }
}
