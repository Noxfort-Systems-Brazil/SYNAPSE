// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { OfficialReportData } from '../../../types/report';
import { useMunicipalSettingsStore } from '../../../stores/useMunicipalSettingsStore';

interface ReportHeaderCardProps {
  report: OfficialReportData;
}

const MONTHS_PT = [
  'janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
  'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro',
];

export const ReportHeaderCard: React.FC<ReportHeaderCardProps> = ({ report }) => {
  const logoDataUrl = useMunicipalSettingsStore((s) => s.logoDataUrl);

  const dateObj = new Date(report.timestamp || Date.now());
  const day = dateObj.getDate();
  const monthName = MONTHS_PT[dateObj.getMonth()];
  const year = dateObj.getFullYear();
  const city = (report as any).city || 'São Paulo';
  const stateUf = (report as any).state_uf || 'SP';
  const officialDateStr = `${city} - ${stateUf}, ${day} de ${monthName} de ${year}`;

  return (
    <div className="space-y-3 text-black font-serif">
      {/* 0. Banner de Rascunho Operacional */}
      <div className="text-center bg-amber-50 border border-amber-300 text-amber-900 text-[10px] py-1 px-2 rounded font-sans italic">
        Aviso Operacional: Documento gerado automaticamente — rascunho técnico até validação pelo Responsável Técnico.
      </div>

      {/* 1. Timbre Oficial do Município (ABNT NBR 10719 / CARINA HeaderBlock) */}
      <div className="text-center space-y-1 pb-2 border-b border-black">
        <div className="flex justify-center mb-1">
          {logoDataUrl ? (
            <div className="h-12 max-w-[160px] flex items-center justify-center">
              <img
                src={logoDataUrl}
                alt="Brasão Oficial da Prefeitura"
                className="max-h-full max-w-full object-contain"
              />
            </div>
          ) : (
            <div className="w-10 h-10 border border-black rounded-full flex flex-col items-center justify-center p-0.5 font-serif text-[7px] font-bold uppercase tracking-wider text-black">
              <span>BRASÃO</span>
            </div>
          )}
        </div>
        <p className="text-[9.5px] uppercase tracking-widest text-black font-semibold">
          República Federativa do Brasil • Poder Executivo Municipal
        </p>
        <h1 className="text-xs font-bold uppercase tracking-wide text-black">
          {report.cityHall}
        </h1>
        <p className="text-[10.5px] font-bold uppercase text-black">
          {report.department}
        </p>
        <p className="text-[9pt] italic text-slate-600">
          Superintendência de Engenharia de Tráfego e Operação Viária • SYNAPSE
        </p>
      </div>

      {/* 2. Praça e Data Oficial por Extenso (CARINA TitleBlock) */}
      <div className="text-right italic text-[10pt] text-slate-700 pt-1">
        {officialDateStr}
      </div>

      {/* 3. Título Principal com Nº de Protocolo (CARINA TitleBlock) */}
      <div className="text-center space-y-0.5 pt-1">
        <h2 className="text-sm font-bold uppercase tracking-tight text-black">
          RELATÓRIO EXPLICATIVO DO SYNAPSE (XAI) Nº {report.protocol}
        </h2>
        <p className="text-[9pt] text-slate-600">
          Processo Administrativo: <strong className="font-mono">{report.processNumber}</strong> • Emissão: {dateObj.toLocaleString('pt-BR')} (UTC-03:00) • Sistema: {report.systemVersion || report.system || 'v2.0 Enterprise'}
        </p>
      </div>

      {/* 4. Ementa Oficial Recuada à Direita (CARINA TitleBlock) */}
      <div className="ml-auto max-w-[65%] text-right italic text-[8.5pt] text-slate-700 py-1">
        Ementa: Relatório Técnico Explicativo de Percepção Viária em Tempo Real, Salvaguardas Operacionais, Atribuição de Pesos de IA (XAI) e Consistência Hidrodinâmica da Malha de Tráfego.
      </div>

      {/* 5. Quadro de Identificação do Sistema e Ambiente Operacional (CARINA MetadataBlock) */}
      <div className="pt-2">
        <div className="font-bold text-[9.5px] uppercase tracking-tight text-black mb-1 border-b border-slate-300 pb-0.5">
          Quadro de Identificação do Sistema e Contexto Operacional
        </div>
        <table className="w-full border-collapse text-[10px] font-sans">
          <tbody>
            <tr className="border-b border-slate-200">
              <td className="py-1 px-2 font-bold w-[35%] bg-slate-50 text-slate-900">Identificador do Gateway:</td>
              <td className="py-1 px-2 text-slate-800">{report.systemVersion || report.system || 'SYNAPSE v2.0 Enterprise'}</td>
            </tr>
            <tr className="border-b border-slate-200">
              <td className="py-1 px-2 font-bold bg-slate-50 text-slate-900">Cenário de Operação / Malha:</td>
              <td className="py-1 px-2 text-slate-800">{report.location.corridorName}</td>
            </tr>
            <tr className="border-b border-slate-200">
              <td className="py-1 px-2 font-bold bg-slate-50 text-slate-900">Motor de Percepção / Fusão:</td>
              <td className="py-1 px-2 text-slate-800">iTransformer + GATv2 Lite (PINO / KSE)</td>
            </tr>
            <tr className="border-b border-slate-200">
              <td className="py-1 px-2 font-bold bg-slate-50 text-slate-900">Processo Administrativo:</td>
              <td className="py-1 px-2 font-mono text-slate-800">{report.processNumber}</td>
            </tr>
            <tr className="border-b border-slate-200">
              <td className="py-1 px-2 font-bold bg-slate-50 text-slate-900">Protocolo Oficial:</td>
              <td className="py-1 px-2 font-mono text-slate-800">{report.protocol}</td>
            </tr>
            <tr className="border-b border-slate-200">
              <td className="py-1 px-2 font-bold bg-slate-50 text-slate-900">Responsável Técnico / Auditor:</td>
              <td className="py-1 px-2 text-slate-800">{report.authorityName} ({report.authorityRole} — {report.registrationNumber})</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};

