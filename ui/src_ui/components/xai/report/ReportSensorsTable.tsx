// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { TrafficSensorItem } from '../../../types/report';

interface ReportSensorsTableProps {
  sensors: TrafficSensorItem[];
}

export const ReportSensorsTable: React.FC<ReportSensorsTableProps> = ({ sensors }) => {
  return (
    <div className="space-y-1.5 font-serif text-black pt-1">
      <div className="border-b border-black pb-0.5">
        <h3 className="text-[11px] font-bold uppercase text-black">
          3. Inventário Metrológico dos Detectores e Equipamentos de Campo
        </h3>
      </div>

      <p className="text-[10px] text-black italic">
        Tabela 1 — Discriminação dos detectores veiculares, equipamentos e grandezas aferidas.
      </p>

      {/* Tabela Padrão IBGE (Laterais Abertas, Linhas Horizontais Claras) */}
      <div className="w-full">
        <table className="w-full table-fixed text-left text-xs border-collapse font-sans">
          <thead>
            <tr className="border-t border-b border-black text-[9.5px] uppercase font-bold text-black">
              <th className="py-1.5 px-1 w-[16%]">Identificação</th>
              <th className="py-1.5 px-1 w-[26%]">Interseção / Local</th>
              <th className="py-1.5 px-1 w-[18%]">Tecnologia</th>
              <th className="py-1.5 px-1 w-[11%] text-right">Velocidade</th>
              <th className="py-1.5 px-1 w-[11%] text-right">Volume</th>
              <th className="py-1.5 px-1 w-[8%] text-right">Sat. (x)</th>
              <th className="py-1.5 px-1 w-[10%]">Laudo</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 text-[10px] font-mono">
            {sensors.map((s) => (
              <tr key={s.id}>
                <td className="py-1 px-1 font-bold text-black truncate">{s.id}</td>
                <td className="py-1 px-1 text-black font-serif text-[10px] truncate">{s.junction}</td>
                <td className="py-1 px-1 text-black font-sans text-[9px] truncate">{s.equipmentType}</td>
                <td className="py-1 px-1 text-right text-black font-bold">{s.measuredSpeed}</td>
                <td className="py-1 px-1 text-right text-black font-bold">{s.measuredFlow}</td>
                <td className="py-1 px-1 text-right font-bold text-black">{s.saturationDegree.split(' ')[0]}</td>
                <td className="py-1 px-1 text-black font-sans text-[9px] truncate">{s.inmetroReport}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="border-t border-black text-[9px] text-black italic font-serif">
              <td colSpan={7} className="py-1 px-1">
                Fonte: Registros metrológicos oficiais da fiscalização de tráfego municipal (Disponibilidade: 98,4%).
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
};
