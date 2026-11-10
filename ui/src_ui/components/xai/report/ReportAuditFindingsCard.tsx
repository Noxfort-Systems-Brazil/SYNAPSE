// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { ShieldCheck, CheckCircle2 } from 'lucide-react';

export const ReportAuditFindingsCard: React.FC = () => {
  const findings = [
    {
      num: '5.1',
      title: 'Classificação e Qualidade das Fontes Sensoriais',
      standard: 'Critérios de Amostragem e Telemetria Viária',
      finding:
        'O sistema distinguiu detectores físicos de campo (radares Doppler e câmeras) e feeds agregados de terceiros (APIs de mobilidade urbana), mantendo telemetria a 1,0 Hz e documentando a disponibilidade real de cada fonte.',
    },
    {
      num: '5.2',
      title: 'Consistência com as Leis de Conservação Macroscópica (LWR / PINO)',
      standard: 'Equação de Continuidade de Lighthill-Whitham-Richards',
      finding:
        'A estimativa do estado de tráfego manteve o resíduo diferencial de continuidade física abaixo do limiar de 0,05, resultado consistente com a dinâmica real da via e indicando plausibilidade física do modelo.',
    },
    {
      num: '5.3',
      title: 'Atuação das Salvaguardas Preventivas e Isolamento de Ruído',
      standard: 'Filtros Preventivos (WaveletAE / PI-DVAE-TCN)',
      finding:
        'As salvaguardas automáticas colocaram leituras com oscilação anômala em quarentena preventiva e atenuaram ruídos de alta frequência na telemetria, protegendo o pipeline contra distorções espúrias.',
    },
    {
      num: '5.4',
      title: 'Explicabilidade dos Pesos por Gradientes Integrados',
      standard: 'Método de Gradientes Integrados (Captum)',
      finding:
        'O método de Gradientes Integrados decompôs a influência relativa de cada grandeza física (velocidade, ocupação, saturação e fluxo) em relação à linha de base neutra, atendendo aos princípios de transparência algorítmica da LGPD.',
    },
    {
      num: '5.5',
      title: 'Estimativa Temporária em Contingência (Dead Reckoning)',
      standard: 'Estimador Cinemático de Estado',
      finding:
        'Durante quedas transitórias de sinal ou perdas momentâneas de pacotes, a projeção cinemática temporária sustentou a continuidade do fluxo sem interrupção do monitoramento.',
    },
  ];

  return (
    <div className="space-y-3 font-serif text-black">
      <div className="border-b border-black pb-0.5">
        <h3 className="text-[11px] font-bold uppercase text-black">
          5. Verificação Física de Tráfego e Salvaguardas Operacionais
        </h3>
        <p className="text-[10px] text-black italic">
          Avaliação técnica de plausibilidade física, tolerância a anomalias e explicabilidade de dados.
        </p>
      </div>

      <div className="space-y-2 text-xs text-justify leading-relaxed">
        {findings.map((f) => (
          <div key={f.num} className="space-y-0.5">
            <p className="text-[10.5px] text-black font-bold">
              {f.num}. {f.title}
            </p>
            <p className="text-[9.5px] text-slate-700 italic">
              <strong>Referência Técnica:</strong> {f.standard}
            </p>
            <p className="indent-4 text-[10px] text-black">
              {f.finding}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
