// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import React from 'react';

interface ReportSignatureCardProps {
  digitalCertification: string;
  operationalSupervision: string;
  authorityName: string;
  authorityRole: string;
  registrationNumber: string;
  department: string;
}

export const ReportSignatureCard: React.FC<ReportSignatureCardProps> = ({
  digitalCertification,
  operationalSupervision,
  authorityName,
  authorityRole,
  registrationNumber,
  department,
}) => {
  return (
    <div className="space-y-4 font-serif text-black">
      <div className="border-b border-black pb-0.5">
        <h3 className="text-[11px] font-bold uppercase text-black">
          10. Parecer Técnico Conclusivo e Encerramento Institucional
        </h3>
      </div>

      <div className="text-xs text-justify leading-relaxed space-y-1.5">
        <p className="indent-6 text-[10.5px] text-black">
          Conclui-se, do ponto de vista técnico e operacional, que a intervenção semafórica adaptativa executada na malha arterial do Corredor Paulista mostrou-se plenamente regular, necessária e eficaz, tendo eliminado a retenção crítica de veículos e preservado integralmente todos os tempos de segurança viária estabelecidos pelas resoluções do CONTRAN.
        </p>
        <p className="indent-6 text-[10.5px] text-black">
          O presente Relatório Técnico Operacional é emitido sob a competência expressa do <strong>Art. 24 do Código de Trânsito Brasileiro (Lei nº 9.503/1997)</strong> e homologado pela equipe técnica de fiscalização e operações de trânsito do município.
        </p>
      </div>

      {/* Bloco Oficial de Assinaturas (Padrão ABNT com Linhas Simples) */}
      <div className="grid grid-cols-2 gap-8 pt-8 pb-4 text-center text-xs">
        <div className="space-y-1">
          <div className="border-t border-black pt-1.5 mx-auto max-w-[220px]">
            <p className="font-bold text-black text-[11px] font-serif">
              {authorityName}
            </p>
            <p className="text-[9.5px] text-black font-sans font-bold">
              {authorityRole}
            </p>
            <p className="text-[9px] text-black font-sans font-mono">
              {registrationNumber}
            </p>
          </div>
        </div>

        <div className="space-y-1">
          <div className="border-t border-black pt-1.5 mx-auto max-w-[220px]">
            <p className="font-bold text-black text-[11px] font-serif">
              Supervisão de Operações de Tráfego
            </p>
            <p className="text-[9.5px] text-black font-sans font-bold">
              {department}
            </p>
            <p className="text-[9px] text-black font-sans">
              Equipe Técnica de Engenharia e Fiscalização Semafórica
            </p>
          </div>
        </div>
      </div>

      {/* Rodapé de Homologação em Texto Simples (Sem Cartão) */}
      <div className="border-t border-b border-black py-1 text-[9.5px] font-mono flex justify-between text-black">
        <span>Certificação do Sistema: <strong>{digitalCertification}</strong></span>
        <span>Regime: {operationalSupervision}</span>
      </div>
    </div>
  );
};
