// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';

interface ReportReferencesCardProps {
  references: string[];
}

export const ReportReferencesCard: React.FC<ReportReferencesCardProps> = ({ references }) => {
  return (
    <div className="space-y-2 font-serif text-black pt-2">
      <div className="border-b border-black pb-0.5">
        <h3 className="text-[11px] font-bold uppercase text-black">
          11. Referências Normativas e Bibliográficas (ABNT NBR 6023:2018)
        </h3>
      </div>

      <div className="text-[9.5px] leading-relaxed text-black text-justify space-y-1.5 pl-0">
        {references.map((ref, idx) => (
          <p key={idx} className="text-black">
            {ref}
          </p>
        ))}
      </div>
    </div>
  );
};
