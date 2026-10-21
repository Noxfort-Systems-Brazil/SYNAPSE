// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { PeritialQuesitoItem } from '../../../types/report';

interface ReportQuesitosCardProps {
  quesitos: PeritialQuesitoItem[];
}

export const ReportQuesitosCard: React.FC<ReportQuesitosCardProps> = ({ quesitos }) => {
  return (
    <div className="space-y-3 font-serif text-black">
      <div className="border-b border-black pb-0.5">
        <h3 className="text-[11px] font-bold uppercase text-black">
          8. Resposta aos Quesitos Técnicos Operacionais
        </h3>
        <p className="text-[10px] text-black italic">
          Respostas objetivas e fundamentadas em estrito atendimento à Norma ABNT NBR 13752:1996 e ao CTB.
        </p>
      </div>

      <div className="space-y-2.5 text-xs text-justify leading-relaxed">
        {quesitos.map((q) => (
          <div key={q.number} className="space-y-0.5">
            <p className="text-[10.5px] text-black font-bold">
              8.{q.number}. Quesito {q.number}: {q.question}
            </p>
            <p className="indent-4 text-[10.5px] text-black">
              <strong>Resposta:</strong> {q.answer}. <strong>Justificativa Técnica:</strong> {q.technicalJustification}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
