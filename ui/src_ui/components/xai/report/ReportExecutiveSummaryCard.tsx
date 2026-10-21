// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { OfficialReportData } from '../../../types/report';

interface ReportExecutiveSummaryCardProps {
  report: OfficialReportData;
}

export const ReportExecutiveSummaryCard: React.FC<ReportExecutiveSummaryCardProps> = ({ report }) => {
  const evolution = report.comparativeEvolution;
  const hasComp = evolution && evolution.hasPrevious;

  return (
    <div className="space-y-4 font-serif text-black pt-2">
      {/* Título de Seção Primária (ABNT NBR 6024) */}
      <div className="border-b border-black pb-1">
        <h2 className="text-xs font-bold uppercase tracking-wider text-black">
          PARTE I — SUMÁRIO EXECUTIVO PARA GESTÃO PÚBLICA
        </h2>
        <p className="text-[10px] text-black italic">
          Síntese de alto nível dos resultados operacionais, mitigação de congestionamentos e auditoria metrológica de sensores.
        </p>
      </div>

      {/* 1. Objetivo da Gestão e Auditoria Metrológica */}
      <div className="space-y-1 text-xs text-justify leading-relaxed">
        <h3 className="font-bold text-[11px] text-black">
          1. Objetivo da Gestão e Auditoria Metrológica
        </h3>
        <p className="indent-6 text-[11px] text-black">
          {report.auditObjective ||
            'Auditar a consistência metrológica da fusão neural de sensores em tempo real na malha arterial, fiscalizando o cumprimento das leis de conservação física do fluxo veicular e explicabilidade algorítmica.'}
        </p>
      </div>

      {/* 2. Principais Destaques Operacionais */}
      <div className="space-y-1.5 text-xs">
        <h3 className="font-bold text-[11px] text-black">
          2. Principais Destaques Operacionais da Telemetria Ao Vivo
        </h3>
        <ul className="space-y-1 text-[11px] text-black text-justify pl-4 list-none leading-relaxed">
          <li>
            <strong>a) Volume Total Agregado:</strong> {report.networkSummary.totalHourlyFlow} na malha viária monitorada;
          </li>
          <li>
            <strong>b) Velocidade Média Espacial Estimada:</strong> {report.networkSummary.networkMeanSpeed} via fusão sensorial e modelos de tráfego;
          </li>
          <li>
            <strong>c) Estado e Saturação da Malha:</strong> {report.networkSummary.networkLevelOfService} (Grau de Saturação Médio: {report.networkSummary.networkMeanSaturation});
          </li>
          <li>
            <strong>d) Integridade e Sensores Ativos:</strong> {report.sensors.length} detectores em operação normal com validação Zero-Trust ativa.
          </li>
        </ul>
      </div>

      {/* 3. Quadro-Síntese Comparativo (Tabela Padrão IBGE com Laterais Abertas) */}
      <div className="space-y-1.5 text-xs pt-1">
        <h3 className="font-bold text-[11px] text-black">
          3. Quadro-Síntese de Evolução Temporal (Pasta Synapse)
        </h3>

        <div className="w-full">
          {hasComp ? (
            <table className="w-full text-left text-xs border-collapse font-sans">
              <thead>
                <tr className="border-t border-b border-black text-[10px] uppercase font-bold text-black">
                  <th className="py-2 px-1 w-[38%]">Indicador Metrológico</th>
                  <th className="py-2 px-1 w-[20%] text-right">Snapshot Anterior</th>
                  <th className="py-2 px-1 w-[20%] text-right">Telemetria Atual</th>
                  <th className="py-2 px-1 w-[22%] text-right">Variação (Δ)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-[10.5px]">
                <tr>
                  <td className="py-1.5 px-1 font-serif text-black">Velocidade Média Espacial</td>
                  <td className="py-1.5 px-1 text-right font-mono text-black">{evolution.previousSpeed.toFixed(1)} km/h</td>
                  <td className="py-1.5 px-1 text-right font-mono font-bold text-black">{evolution.currentSpeed.toFixed(1)} km/h</td>
                  <td className="py-1.5 px-1 text-right font-mono font-bold text-black">
                    {evolution.deltaSpeed >= 0 ? '+' : ''}{evolution.deltaSpeed.toFixed(1)} km/h ({evolution.percentChangeSpeed >= 0 ? '+' : ''}{evolution.percentChangeSpeed.toFixed(1)}%)
                  </td>
                </tr>
                <tr>
                  <td className="py-1.5 px-1 font-serif text-black">Volume de Fluxo Veicular</td>
                  <td className="py-1.5 px-1 text-right font-mono text-black">{evolution.previousFlow.toFixed(0)} veíc/h</td>
                  <td className="py-1.5 px-1 text-right font-mono font-bold text-black">{evolution.currentFlow.toFixed(0)} veíc/h</td>
                  <td className="py-1.5 px-1 text-right font-mono font-bold text-black">
                    {evolution.deltaFlow >= 0 ? '+' : ''}{evolution.deltaFlow.toFixed(0)} veíc/h ({evolution.percentChangeFlow >= 0 ? '+' : ''}{evolution.percentChangeFlow.toFixed(1)}%)
                  </td>
                </tr>
                <tr>
                  <td className="py-1.5 px-1 font-serif text-black">Grau de Saturação ($x = V/c$)</td>
                  <td className="py-1.5 px-1 text-right font-mono text-black">{evolution.previousSaturation.toFixed(2)}</td>
                  <td className="py-1.5 px-1 text-right font-mono font-bold text-black">{evolution.currentSaturation.toFixed(2)}</td>
                  <td className="py-1.5 px-1 text-right font-mono font-bold text-black">
                    {evolution.deltaSaturation >= 0 ? '+' : ''}{evolution.deltaSaturation.toFixed(2)}
                  </td>
                </tr>
                <tr>
                  <td className="py-1.5 px-1 font-serif text-black">Regime Macroscópico de Tráfego</td>
                  <td className="py-1.5 px-1 text-right font-mono text-black">{evolution.previousFlowRegime}</td>
                  <td className="py-1.5 px-1 text-right font-mono font-bold text-black">{evolution.currentFlowRegime}</td>
                  <td className="py-1.5 px-1 text-right font-sans font-bold text-black">
                    {evolution.previousFlowRegime === evolution.currentFlowRegime ? 'Estável' : 'Transição Dinâmica'}
                  </td>
                </tr>
                <tr>
                  <td className="py-1.5 px-1 font-serif text-black">Detectores Ativos em Rede</td>
                  <td className="py-1.5 px-1 text-right font-mono text-black">{evolution.previousSensorsCount} detectores</td>
                  <td className="py-1.5 px-1 text-right font-mono font-bold text-black">{evolution.currentSensorsCount} detectores</td>
                  <td className="py-1.5 px-1 text-right font-mono font-bold text-black">
                    {evolution.currentSensorsCount - evolution.previousSensorsCount >= 0 ? '+' : ''}{evolution.currentSensorsCount - evolution.previousSensorsCount}
                  </td>
                </tr>
              </tbody>
              <tfoot>
                <tr className="border-t border-black text-[9.5px] text-black italic font-serif">
                  <td colSpan={4} className="py-1.5 px-1">
                    {evolution.summaryText}
                  </td>
                </tr>
              </tfoot>
            </table>
          ) : (
            <table className="w-full text-left text-xs border-collapse font-sans">
              <thead>
                <tr className="border-t border-b border-black text-[10px] uppercase font-bold text-black">
                  <th className="py-2 px-1 w-[40%]">Indicador Metrológico</th>
                  <th className="py-2 px-1 w-[25%] text-right">Telemetria Ao Vivo</th>
                  <th className="py-2 px-1 w-[35%] text-right">Condição Operacional</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-[10.5px]">
                <tr>
                  <td className="py-1.5 px-1 font-serif text-black">Velocidade Média Espacial</td>
                  <td className="py-1.5 px-1 text-right font-mono font-bold text-black">{report.networkSummary.networkMeanSpeed}</td>
                  <td className="py-1.5 px-1 text-right font-sans text-black">Linha de Base Inicial</td>
                </tr>
                <tr>
                  <td className="py-1.5 px-1 font-serif text-black">Volume de Fluxo Veicular</td>
                  <td className="py-1.5 px-1 text-right font-mono font-bold text-black">{report.networkSummary.totalHourlyFlow}</td>
                  <td className="py-1.5 px-1 text-right font-sans text-black">Fluxo em Monitoramento</td>
                </tr>
                <tr>
                  <td className="py-1.5 px-1 font-serif text-black">Grau de Saturação ($x = V/c$)</td>
                  <td className="py-1.5 px-1 text-right font-mono font-bold text-black">{report.networkSummary.networkMeanSaturation}</td>
                  <td className="py-1.5 px-1 text-right font-sans text-black">{report.networkSummary.networkLevelOfService}</td>
                </tr>
                <tr>
                  <td className="py-1.5 px-1 font-serif text-black">Detectores Ativos em Rede</td>
                  <td className="py-1.5 px-1 text-right font-mono font-bold text-black">{report.sensors.length} detectores</td>
                  <td className="py-1.5 px-1 text-right font-sans text-black">Zero-Trust Sanitizado</td>
                </tr>
              </tbody>
              <tfoot>
                <tr className="border-t border-black text-[9.5px] text-black italic font-serif">
                  <td colSpan={3} className="py-1.5 px-1">
                    Fonte: Linha de base metrológica inicial gravada na pasta Synapse (Arquivo: last_traffic_snapshot.json). O cálculo de evolução temporal comparativa será ativado na próxima emissão de laudo.
                  </td>
                </tr>
              </tfoot>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};
