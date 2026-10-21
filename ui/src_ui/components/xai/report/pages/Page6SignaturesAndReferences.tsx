// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { OfficialReportData } from '../../../../types/report';
import { ReportSignatureCard } from '../ReportSignatureCard';
import { ReportReferencesCard } from '../ReportReferencesCard';

interface PageProps {
  report: OfficialReportData;
  pageNumber: number;
  totalPages: number;
}

export const Page6SignaturesAndReferences: React.FC<PageProps> = ({ report, pageNumber, totalPages }) => {
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

        {/* 10. Parecer Técnico Conclusivo e Encerramento Institucional */}
        <ReportSignatureCard
          digitalCertification={report.digitalCertification || 'CERTIFICADO-OPERACIONAL-HOMOLOGADO'}
          operationalSupervision={report.operationalSupervision}
          authorityName={report.authorityName}
          authorityRole={report.authorityRole}
          registrationNumber={report.registrationNumber}
          department={report.department}
        />

        {/* 11. Referências Normativas e Bibliográficas (ABNT NBR 6023) */}
        <ReportReferencesCard references={report.references} />
      </div>

      {/* Rodapé Padronizado ABNT com Termo de Encerramento */}
      <div className="pt-3 border-t border-black flex justify-between items-center text-[9.5px] text-black font-sans">
        <span>Processo: <strong>{report.processNumber}</strong> • Protocolo: {report.protocol}</span>
        <span className="font-bold">Folha {pageNumber} de {totalPages} (Termo de Encerramento)</span>
      </div>
    </div>
  );
};
