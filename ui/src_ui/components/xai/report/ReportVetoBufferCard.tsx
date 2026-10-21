// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { TrafficSafetyInterventionItem } from '../../../types/report';

interface ReportVetoBufferCardProps {
  vetoHistory: TrafficSafetyInterventionItem[];
}

export const ReportVetoBufferCard: React.FC<ReportVetoBufferCardProps> = ({ vetoHistory }) => {
  return (
    <div className="space-y-3 font-serif text-black">
      <div className="border-b border-black pb-0.5">
        <h3 className="text-[11px] font-bold uppercase text-black">
          4. Auditoria de Segurança Viária & Atuação de Guardrails do CONTRAN
        </h3>
        <p className="text-[10px] text-black italic">
          Registro das intervenções de segurança, imposição de tempos mínimos regulamentares e retificações de controle.
        </p>
      </div>

      <div className="space-y-3 text-xs leading-relaxed">
        {vetoHistory.map((item, idx) => (
          <div key={item.id} className="space-y-1 text-justify">
            <h4 className="font-bold text-[10.5px] text-black">
              4.{idx + 1}. Intervenção {item.id} — {item.junction} ({item.timeRecorded})
            </h4>
            <p className="indent-4 text-[10.5px] text-black">
              <strong>Equipamento / Sensor:</strong> {item.equipmentId}.{' '}
              <strong>Dispositivo Normativo:</strong> {item.contranStandardViolated}.
            </p>
            <p className="indent-4 text-[10.5px] text-black">
              <strong>Irregularidade Detectada:</strong> {item.irregularityDetected}
            </p>
            <p className="indent-4 text-[10.5px] text-black">
              <strong>Ação Protetiva Aplicada:</strong> {item.correctiveGuardrail} (Status: <em>{item.finalState}</em>).
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
