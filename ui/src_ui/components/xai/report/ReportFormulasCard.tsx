// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';
import { LatexRenderer } from '../../common/LatexRenderer';

interface ReportFormulasCardProps {
  convergenceDelta?: number;
}

export const ReportFormulasCard: React.FC<ReportFormulasCardProps> = () => {
  return (
    <div className="space-y-3 font-serif text-black">
      <div className="border-b border-black pb-0.5">
        <h3 className="text-[11px] font-bold uppercase text-black">
          ANEXO TÉCNICO: Memorial de Cálculo e Formulações de Percepção
        </h3>
        <p className="text-[10px] text-black italic">
          Formulações canônicas de dinâmica macroscópica, conservação física PINO, fusão neural e explicabilidade.
        </p>
      </div>

      <div className="space-y-2.5 text-xs text-justify leading-relaxed">
        {/* Equação A.1: Grau de Saturação e Fluxo Fundamental (HCM) */}
        <div className="space-y-0.5">
          <p className="font-bold text-[10.5px] text-black">
            A.1. Grau de Saturação e Relação Fundamental de Fluxo (Highway Capacity Manual — HCM)
          </p>
          <p className="indent-4 text-[10px] text-black">
            A caracterização macroscópica relaciona o volume aferido <LatexRenderer math="V" displayMode={false} /> à capacidade <LatexRenderer math="c" displayMode={false} />, e a taxa de fluxo <LatexRenderer math="q" displayMode={false} /> à densidade espacial <LatexRenderer math="\rho" displayMode={false} /> e velocidade <LatexRenderer math="v" displayMode={false} />:
          </p>
          <div className="py-1 text-center">
            <LatexRenderer
              math="x = \frac{V}{c}, \quad q = \rho \cdot v \tag{A.1}"
              displayMode={true}
            />
          </div>
        </div>

        {/* Equação A.2: Conservação Macroscópica de Tráfego (LWR / PINO) */}
        <div className="space-y-0.5">
          <p className="font-bold text-[10.5px] text-black">
            A.2. Equação Diferencial Parcial de Continuidade de Tráfego (LWR / PINO)
          </p>
          <p className="indent-4 text-[10px] text-black">
            Garante a conservação física estrita de massa veicular sem criação ou destruição fictícia de fluxo ao longo da via:
          </p>
          <div className="py-1 text-center">
            <LatexRenderer
              math="\frac{\partial \rho}{\partial t} + \frac{\partial (\rho \cdot v(\rho))}{\partial x} = 0, \quad v(\rho) = v_f \left(1 - \frac{\rho}{\rho_{\text{jam}}}\right) \tag{A.2}"
              displayMode={true}
            />
          </div>
        </div>

        {/* Equação A.3: Fusão Multivariada por Atenção Cruzada (iTransformer) */}
        <div className="space-y-0.5">
          <p className="font-bold text-[10.5px] text-black">
            A.3. Fusão Multivariada por Atenção Invertida Inter-Sensores (iTransformer)
          </p>
          <p className="indent-4 text-[10px] text-black">
            Mapeia as correlações mútuas entre séries temporais de detectores heterogêneos da malha arterial:
          </p>
          <div className="py-1 text-center">
            <LatexRenderer
              math="\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{Q K^T}{\sqrt{d_{\text{model}}}}\right) V \tag{A.3}"
              displayMode={true}
            />
          </div>
        </div>

        {/* Equação A.4: Gradientes Integrados e Axioma da Completude (Captum) */}
        <div className="space-y-0.5">
          <p className="font-bold text-[10.5px] text-black">
            A.4. Atribuição por Gradientes Integrados e Axioma da Completude (Captum)
          </p>
          <p className="indent-4 text-[10px] text-black">
            Decomposição matemática da contribuição de cada variável sensorial para a estimativa de tráfego, distribuindo a variação em relação à linha de base neutra:
          </p>
          <div className="py-1 text-center">
            <LatexRenderer
              math="\sum_{i=1}^{n} \text{IG}_i(x) = \sum_{i=1}^{n} (x_i - x'_i) \cdot \int_{0}^{1} \frac{\partial F(x' + \alpha(x - x'))}{\partial x_i} d\alpha = F(x) - F(x') \tag{A.4}"
              displayMode={true}
            />
          </div>
        </div>

        {/* Equação A.5: Estimador Cinemático de Estado (Dead Reckoning com Amortecimento) */}
        <div className="space-y-0.5">
          <p className="font-bold text-[10.5px] text-black">
            A.5. Estimador Cinemático de Estado para Tolerância a Falhas (Dead Reckoning com Amortecimento)
          </p>
          <p className="indent-4 text-[10px] text-black">
            Preserva a continuidade temporal do fluxo por inércia newtoniana amortecida em casos de perda temporária de pacotes de dados:
          </p>
          <div className="py-1 text-center">
            <LatexRenderer
              math="v_t = v_{t-1} + a_{t-1} \cdot \Delta t \cdot e^{-\lambda \Delta t} \tag{A.5}"
              displayMode={true}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
