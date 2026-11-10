// SPDX-License-Identifier: AGPL-3.0-or-later
// SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import {
  TrafficSensorItem,
  TrafficSafetyInterventionItem,
  TrafficAttributionItem,
  PeritialQuesitoItem,
  LegalFramingItem,
  ReportLocationData,
  TrafficNetworkMacroSummary,
} from '../../types/report';
import {
  MOCK_REPORT_LOCATION,
  MOCK_NETWORK_SUMMARY,
  MOCK_SENSORS,
  MOCK_SAFETY_INTERVENTIONS,
  MOCK_ATTRIBUTIONS,
  MOCK_QUESITOS,
  MOCK_LEGAL_FRAMING,
  MOCK_REFERENCES,
} from './trafficAuditMockData';

/**
 * Pure Backend DTO contract simulating what the Rust/Python backend returns.
 * Completely free of frontend UI strings or state variables.
 */
export interface BackendReportPayload {
  systemVersion: string;
  auditObjective: string;
  observedTrafficDiagnosis: string;
  adaptiveActionExecuted: string;
  location: ReportLocationData;
  networkSummary: TrafficNetworkMacroSummary;
  sensors: TrafficSensorItem[];
  safetyInterventions: TrafficSafetyInterventionItem[];
  attributions: TrafficAttributionItem[];
  counterfactualAnalysis: string;
  quesitos: PeritialQuesitoItem[];
  legalFraming: LegalFramingItem[];
  references: string[];
  operationalSupervision: string;
  digitalCertification: string;
}

export const getMockBackendReportPayload = (): BackendReportPayload => {
  return {
    systemVersion: 'SYNAPSE v2.0 Enterprise (Módulo de Controle Semafórico Adaptativo em Malha Arterial)',
    auditObjective:
      'Realizar a auditoria técnica e verificação de conformidade na operação semafórica adaptativa em tempo real na malha arterial do Corredor Paulista, fiscalizando o cumprimento dos tempos mínimos de segurança do CONTRAN, o dimensionamento de saturação e a fundamentação da reprogramação dinâmica de tempos de verde.',
    observedTrafficDiagnosis:
      'Durante a supervisão operacional no intervalo de pico das 18h00, constatou-se a formação de onda de choque de retardo a montante no eixo arterial da Av. Paulista, com grau de saturação atingindo x = 0,92 e taxa de ocupação dos detectores em 89,2%. A velocidade média caiu para 12,4 km/h, caracterizando regime de fluxo forçado e iminência de bloqueio das interseções transversais na Rua Augusta e Alameda Santos.',
    adaptiveActionExecuted:
      'Execução da intervenção semafórica dinâmica pelo sistema adaptativo, com aplicação de extensão de 15 segundos no tempo de verde efetivo do Estágio 1 (Av. Paulista), reescalonamento da defasagem (offset) nas interseções adjacentes e manutenção inviolável dos tempos de segurança: tempo de amarelo de 4,0 segundos e tempo de pedestre de 18,0 segundos.',
    location: MOCK_REPORT_LOCATION,
    networkSummary: MOCK_NETWORK_SUMMARY,
    sensors: MOCK_SENSORS,
    safetyInterventions: MOCK_SAFETY_INTERVENTIONS,
    attributions: MOCK_ATTRIBUTIONS,
    counterfactualAnalysis:
      'A intervenção semafórica dinâmica seria dispensada (mantendo-se o plano semafórico estático nominal de 120s) se, e somente se, o grau de saturação na aproximação principal regredisse para x < 0,65 (valor observado: x = 0,92) OU a velocidade média na via arterial superasse 30,0 km/h (velocidade observada: 12,4 km/h).',
    quesitos: MOCK_QUESITOS,
    legalFraming: MOCK_LEGAL_FRAMING,
    references: MOCK_REFERENCES,
    operationalSupervision: 'Operação Centralizada e Supervisionada pelo CCO — Regime de Alta Eficiência e Segurança Viária',
    digitalCertification: 'CERTIFICADO-OPERACIONAL-SMT-HOMOLOGADO',
  };
};
