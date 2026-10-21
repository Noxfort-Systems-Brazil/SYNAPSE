// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { LegalFramingItem } from '../../../types/report';

interface ReportLegalCardProps {
  legalFraming: LegalFramingItem[];
}

export const ReportLegalCard: React.FC<ReportLegalCardProps> = ({ legalFraming }) => {
  return (
    <div className="space-y-2.5 font-serif text-black pt-2">
      <div className="border-b border-black pb-0.5">
        <h3 className="text-[11px] font-bold uppercase text-black">
          9. Enquadramento Normativo e Fundamentação Jurídico-Administrativa
        </h3>
        <p className="text-[10px] text-black italic">
          Legislação federal de trânsito, competência municipal do CTB, resoluções do CONTRAN e transparência pública.
        </p>
      </div>

      <div className="space-y-2 text-xs text-justify leading-relaxed">
        {legalFraming.map((legal, idx) => (
          <div key={idx} className="space-y-0.5">
            <p className="text-[10.5px] text-black font-bold">
              9.{idx + 1}. {legal.article}
            </p>
            <p className="indent-4 text-[10.5px] text-black">
              {legal.desc}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
