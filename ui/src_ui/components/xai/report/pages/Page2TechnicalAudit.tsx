// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { OfficialReportData } from '../../../../types/report';
import { ReportNetworkSummaryCard } from '../ReportNetworkSummaryCard';
import { ReportSensorsTable } from '../ReportSensorsTable';

interface PageProps {
  report: OfficialReportData;
  pageNumber: number;
  totalPages: number;
}

export const Page2TechnicalAudit: React.FC<PageProps> = ({ report, pageNumber, totalPages }) => {
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

        {/* Título Principal da Parte II */}
        <div className="border-b border-black pb-1">
          <h2 className="text-xs font-bold uppercase tracking-wider text-black">
            PARTE II — RELATÓRIO TÉCNICO E AUDITORIA DA MALHA DE SENSORES E FUSÃO NEURAL
          </h2>
          <p className="text-[10px] text-black italic">
            Fundamentação pericial analítica, inventário metrológico e conformidade normativa (CTB Art. 24).
          </p>
        </div>

        {/* 1. Preâmbulo e Objeto da Perícia Técnica (Texto corrido puro) */}
        <div className="space-y-2">
          <div className="border-b border-black pb-0.5">
            <h3 className="text-[11px] font-bold uppercase text-black">
              1. Preâmbulo e Objeto da Auditoria Técnica
            </h3>
          </div>

          <div className="space-y-1.5 text-xs text-justify leading-relaxed">
            <p className="indent-6 text-[10.5px] text-black">
              <strong>1.1. Objeto da Auditoria:</strong> {report.auditObjective}
            </p>
            <p className="indent-6 text-[10.5px] text-black">
              <strong>1.2. Diagnóstico Operacional do Tráfego:</strong> {report.observedTrafficDiagnosis}
            </p>
            <p className="indent-6 text-[10.5px] text-black">
              <strong>1.3. Ação de Fusão e Tratamento de Telemetria Executada:</strong> {report.adaptiveActionExecuted}
            </p>
            <p className="indent-6 text-[10.5px] text-black">
              <strong>1.4. Caracterização do Local:</strong> {report.location.corridorName} • {report.location.centralNodes}.
            </p>
          </div>
        </div>

        {/* 2. Panorama Macroscópico da Malha Arterial (HCM) */}
        <ReportNetworkSummaryCard
          summary={report.networkSummary}
          location={report.location}
        />

        {/* 3. Inventário Metrológico dos Detectores e Equipamentos de Campo */}
        <ReportSensorsTable sensors={report.sensors} />
      </div>

      {/* Rodapé Padronizado ABNT */}
      <div className="pt-3 border-t border-black flex justify-between items-center text-[9.5px] text-black font-sans">
        <span>Processo: <strong>{report.processNumber}</strong> • Protocolo: {report.protocol}</span>
        <span className="font-bold">Folha {pageNumber} de {totalPages}</span>
      </div>
    </div>
  );
};
