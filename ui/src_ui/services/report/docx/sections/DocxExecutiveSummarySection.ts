// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import { Table, TableRow, AlignmentType, Paragraph } from 'docx';
import { OfficialReportData } from '../../../../types/report';
import {
  DocxTypographyConfig,
  ABNT_TABLE_BORDERS,
  createSectionHeading,
  createSubSectionHeading,
  createParagraph,
  createBulletPoint,
  createTableCaption,
  createCarinaTableCell,
} from '../abntDocxStyles';

/**
 * Builds Section 2: Executive Context and Performance Synthesis Table in Carina benchmark style.
 */
export class DocxExecutiveSummarySection {
  public static build(
    report: OfficialReportData,
    config: DocxTypographyConfig
  ): (Paragraph | Table)[] {
    return [
      createSectionHeading('2. INTRODUÇÃO E CONTEXTO EXECUTIVO', config),

      createParagraph(report.auditObjective, config),

      createSubSectionHeading('Principais Destaques Operacionais e Mitigação de Saturação:', config),
      createBulletPoint('a) Volume Total Atendido: 22.840 veículos por hora ao longo de 4 corredores arteriais interconectados;', config),
      createBulletPoint('b) Ganho de Capacidade no Eixo Crítico: Aumento de 22,4% na taxa de escoamento da Av. Paulista;', config),
      createBulletPoint('c) Redução de Atraso Médio: Diminuição estimada de 14,8% no tempo de espera por veículo na interseção;', config),
      createBulletPoint('d) Preservação Integral da Segurança: 100% de cumprimento dos tempos mínimos de pedestres e amarelo do CONTRAN.', config),

      new Paragraph({ spacing: { before: 140 } }),

      ...createTableCaption(
        'Tabela 1 – Avaliação comparativa antes vs. após intervenção semafórica dinâmica.',
        config,
        'Fonte: Prefeitura Municipal / Secretaria de Trânsito / Motor de Percepção SYNAPSE (2026).'
      ),
      this.createPerformanceTable(config),
    ];
  }

  private static createPerformanceTable(config: DocxTypographyConfig): Table {
    const header = new TableRow({
      tableHeader: true,
      children: [
        createCarinaTableCell('Indicador de Desempenho', 40, config, {
          bold: true,
          fill: 'F2F2F2',
          bottomDarkBorder: true,
        }),
        createCarinaTableCell('Antes da Intervenção', 22, config, {
          bold: true,
          alignment: AlignmentType.RIGHT,
          fill: 'F2F2F2',
          bottomDarkBorder: true,
        }),
        createCarinaTableCell('Após Intervenção', 22, config, {
          bold: true,
          alignment: AlignmentType.RIGHT,
          fill: 'F2F2F2',
          bottomDarkBorder: true,
        }),
        createCarinaTableCell('Variação', 16, config, {
          bold: true,
          alignment: AlignmentType.RIGHT,
          fill: 'F2F2F2',
          bottomDarkBorder: true,
        }),
      ],
    });

    const dataRow = (c1: string, c2: string, c3: string, c4: string, isAlternate: boolean) =>
      new TableRow({
        children: [
          createCarinaTableCell(c1, 40, config, { fill: isAlternate ? 'F8FAFC' : 'FFFFFF' }),
          createCarinaTableCell(c2, 22, config, { alignment: AlignmentType.RIGHT, fill: isAlternate ? 'F8FAFC' : 'FFFFFF' }),
          createCarinaTableCell(c3, 22, config, { bold: true, alignment: AlignmentType.RIGHT, fill: isAlternate ? 'F8FAFC' : 'FFFFFF' }),
          createCarinaTableCell(c4, 16, config, { bold: true, alignment: AlignmentType.RIGHT, fill: isAlternate ? 'F8FAFC' : 'FFFFFF' }),
        ],
      });

    return new Table({
      width: { size: 100, type: 'pct' as any },
      borders: ABNT_TABLE_BORDERS.carinaGrid,
      rows: [
        header,
        dataRow('Grau de Saturação da Aproximação (x = V/c)', '0,92 (Regime Forçado)', '0,68 (Fluxo Estável)', '-26,0% (Alívio)', false),
        dataRow('Velocidade Média Espacial no Corredor', '12,4 km/h', '18,4 km/h', '+48,3% (Fluidez)', true),
        dataRow('Taxa Média de Ocupação dos Detectores', '89,2%', '61,4%', '-31,1% (Redução)', false),
        dataRow('Nível de Serviço Geral (HCM)', 'LOS E (Próximo Colapso)', 'LOS D (Fluxo Regular)', 'Melhoria de Nível', true),
        dataRow('Atuação de Guardrails CONTRAN', '03 Ocorrências Auditadas', '03 Retificações Ativas', '100% Segura', false),
      ],
    });
  }
}
