// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { TrafficAttributionItem } from '../../../types/report';
import { LatexRenderer } from '../../common/LatexRenderer';

interface ReportAttributionListProps {
  attributions: TrafficAttributionItem[];
}

export const ReportAttributionList: React.FC<ReportAttributionListProps> = ({ attributions }) => {
  return (
    <div className="space-y-1.5 font-serif text-black pt-2">
      <div className="border-b border-black pb-0.5">
        <h3 className="text-[11px] font-bold uppercase text-black">
          5. Decomposição Analítica e Atribuição Causal de Demanda de Tráfego
        </h3>
      </div>

      <p className="text-[10px] text-black italic">
        Tabela 2 — Sensibilidade e peso causal das variáveis de tráfego na reprogramação semafórica.
      </p>

      <div className="w-full">
        <table className="w-full table-fixed text-left text-xs border-collapse font-sans">
          <thead>
            <tr className="border-t border-b border-black text-[9.5px] uppercase font-bold text-black">
              <th className="py-1.5 px-1 w-[8%]">Var.</th>
              <th className="py-1.5 px-1 w-[36%]">Parâmetro de Tráfego / Local</th>
              <th className="py-1.5 px-1 w-[16%]">Detector</th>
              <th className="py-1.5 px-1 w-[12%] text-right">Peso (%)</th>
              <th className="py-1.5 px-1 w-[28%]">Impacto na Intervenção</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 text-[10px]">
            {attributions.map((attr, idx) => (
              <tr key={idx}>
                <td className="py-1.5 px-1 font-mono font-bold text-black">
                  <LatexRenderer math={`x_{${idx + 1}}`} displayMode={false} />
                </td>
                <td className="py-1.5 px-1 text-black font-serif">
                  <div className="font-semibold text-[10.5px]">{attr.parameterName}</div>
                  <div className="text-[9px] text-slate-700 font-sans">{attr.junctionLocation}</div>
                </td>
                <td className="py-1.5 px-1 font-mono text-black text-[9.5px]">
                  {attr.detectorId}
                </td>
                <td className="py-1.5 px-1 text-right font-mono font-bold text-black">
                  {attr.gradientDirection.includes('+') ? '+' : '-'}{attr.causalWeightPercent.toFixed(1)}%
                </td>
                <td className="py-1.5 px-1 text-black text-[9.5px] font-serif">
                  {attr.trafficImpactAnalysis}
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="border-t border-black text-[9px] text-black italic font-serif">
              <td colSpan={5} className="py-1 px-1">
                Fonte: Cálculo de gradientes integrados e sensibilidade segundo o Highway Capacity Manual.
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
};
