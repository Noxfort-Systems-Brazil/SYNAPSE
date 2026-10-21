// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { OfficialReportData } from '../../../../types/report';
import { ReportFormulasCard } from '../ReportFormulasCard';

interface PageProps {
  report: OfficialReportData;
  pageNumber: number;
  totalPages: number;
}

export const Page4FormulasAndCounterfactual: React.FC<PageProps> = ({ report, pageNumber, totalPages }) => {
  return (
    <div
      className="abnt-a4-page bg-white text-black font-serif shadow-xl mx-auto flex flex-col justify-between"
      style={{
        width: '210mm',
        minHeight: '297mm',
        padding: '25mm 20mm 20mm 25mm',
        boxSizing: 'border-box',
        marginBottom: '20mm',
      }}
    >
      <div className="space-y-4">
        {/* Cabeçalho Sutil de Continuação ABNT */}
        <div className="border-b border-black pb-1 flex justify-between items-center text-[9.5px] text-black font-sans uppercase tracking-wider">
          <span>{report.cityHall} • {report.department}</span>
          <span>{report.processNumber}</span>
        </div>

        {/* 6. Memorial de Cálculo e Formulação Matemática (KaTeX sem caixas) */}
        <ReportFormulasCard />

        {/* 7. Análise Contrafactual (Hipótese de Refutabilidade Técnica em Texto Corrido) */}
        <div className="space-y-1.5 pt-1">
          <div className="border-b border-black pb-0.5">
            <h3 className="text-[11px] font-bold uppercase text-black">
              7. Análise Contrafactual (Hipótese de Refutabilidade Técnica)
            </h3>
          </div>
          <div className="text-xs text-justify leading-relaxed">
            <p className="indent-6 text-[10.5px] text-black">
              <strong>Condição para Manutenção do Plano Estático Nominal:</strong> {report.counterfactualAnalysis}
            </p>
          </div>
        </div>
      </div>

      {/* Rodapé Padronizado ABNT */}
      <div className="pt-3 border-t border-black flex justify-between items-center text-[9.5px] text-black font-sans">
        <span>Processo: <strong>{report.processNumber}</strong> • Protocolo: {report.protocol}</span>
        <span className="font-bold">Folha {pageNumber} de {totalPages}</span>
      </div>
    </div>
  );
};
