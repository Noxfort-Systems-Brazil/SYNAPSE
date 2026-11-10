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

export const MOCK_REPORT_LOCATION: ReportLocationData = {
  corridorName: 'Corredor Arterial Av. Paulista • Eixo de Conexão Consolação / Augusta / Rebouças',
  jurisdiction: 'Município de São Paulo / Área Central / Gerência de Operações Centro',
  centralNodes: '18 Interseções Semafóricas Interconectadas (Nós Centrais: #48102, #48105, #39201, #48099)',
  geographicBounds: 'Coordenadas Centrais: Latitude -23.558712, Longitude -46.660145',
  nominalNetworkCapacity: 'Capacidade Nominal Total da Malha: 28.000 veíc/h (Capacidade de Saturação por Faixa: 1.800 veíc/h)',
  baselineSignalPlan: 'Plano Semafórico Nominal Coordenado de 120 segundos (Tempo de Ciclo Base: Verde Principal 55s, Secundário 35s, Amarelo 4,0s, Vermelho Geral 2,0s)',
};

export const MOCK_NETWORK_SUMMARY: TrafficNetworkMacroSummary = {
  corridorsMonitored: 4,
  controlledIntersections: 18,
  totalSensorsCount: 5,
  networkLengthKm: 14.6,
  networkMeanSpeed: '18,4 km/h',
  networkMeanSaturation: '0,68 (Grau Médio de Saturação)',
  totalHourlyFlow: '22.840 veíc/h',
  networkLevelOfService: 'Nível de Serviço D / E (Regime de Pico de Tráfego - Highway Capacity Manual)',
};

export const MOCK_SENSORS: TrafficSensorItem[] = [
  {
    id: 'DET-SP-PAULISTA-01',
    junction: 'Av. Paulista x Rua Augusta (Aproximação Sul)',
    equipmentType: 'Detector Laço Indutivo Duplo Eletromagnético',
    measuredSpeed: '12,4 km/h',
    measuredFlow: '1.450 veíc/h',
    saturationDegree: '0,92 (Regime Forçado)',
    occupancyRate: '89,2%',
    inmetroReport: 'Laudo INMETRO nº 8941/2025 (Válido)',
    operationalStatus: 'Operação Nominal',
  },
  {
    id: 'DET-SP-AUGUSTA-02',
    junction: 'Rua Augusta x Alameda Santos',
    equipmentType: 'Detector Não-Intrusivo / Visão Computacional OCR',
    measuredSpeed: '18,1 km/h',
    measuredFlow: '680 veíc/h',
    saturationDegree: '0,48 (Fluxo Estável)',
    occupancyRate: '42,5%',
    inmetroReport: 'Certificado de Aferição nº 7812/2025',
    operationalStatus: 'Operação Nominal',
  },
  {
    id: 'RAD-SP-REBOUCAS-03',
    junction: 'Av. Rebouças x Av. Brasil',
    equipmentType: 'Radar Doppler de Micro-ondas / Velocímetro',
    measuredSpeed: '34,2 km/h',
    measuredFlow: '2.100 veíc/h',
    saturationDegree: '0,74 (Próximo à Capacidade)',
    occupancyRate: '58,0%',
    inmetroReport: 'Portaria INMETRO/SUR-SP nº 9934/2025',
    operationalStatus: 'Operação Nominal',
  },
  {
    id: 'DET-SP-CONSOLACAO-04',
    junction: 'Rua da Consolação x Av. Paulista',
    equipmentType: 'Detector Laço Indutivo em Placa de Trânsito',
    measuredSpeed: '14,0 km/h',
    measuredFlow: '1.120 veíc/h',
    saturationDegree: '0,84 (Regime Saturado)',
    occupancyRate: '76,0%',
    inmetroReport: 'Laudo de Calibração nº 4512/2025',
    operationalStatus: 'Operação Nominal',
  },
  {
    id: 'DET-SP-9DEJULHO-05',
    junction: 'Av. 9 de Julho x Rua Peixoto Gomide',
    equipmentType: 'Detector Eletromagnético Volumétrico',
    measuredSpeed: '22,6 km/h',
    measuredFlow: '1.890 veíc/h',
    saturationDegree: '0,66 (Fluxo Regular)',
    occupancyRate: '61,4%',
    inmetroReport: 'Laudo INMETRO nº 6541/2025 (Válido)',
    operationalStatus: 'Operação Nominal',
  },
];

export const MOCK_SAFETY_INTERVENTIONS: TrafficSafetyInterventionItem[] = [
  {
    id: 'INT-SEG-01',
    timeRecorded: '18:14:22',
    junction: 'Av. Rebouças x Av. Brasil',
    equipmentId: 'RAD-SP-REBOUCAS-03',
    irregularityDetected: 'Discrepância instrumental de leitura pontual de velocidade (ruído instantâneo no feixe Doppler).',
    trafficSafetyRisk: 'Risco de falso acionamento de plano de retenção semafórica emergencial.',
    contranStandardViolated: 'Critério de Confiabilidade Metrológica da Resolução CONTRAN nº 798/2020.',
    correctiveGuardrail: 'Filtro de consistência física rejeitou a leitura espúria e manteve a programação semafórica coordenada.',
    finalState: 'INTERVENÇÃO HOMOLOGADA',
  },
  {
    id: 'INT-SEG-02',
    timeRecorded: '18:22:45',
    junction: 'Av. Paulista x Rua Augusta',
    equipmentId: 'CONTROLADOR_ATU_PAULISTA',
    irregularityDetected: 'Tentativa de corte prematuro de tempo de verde pelo otimizador de fluxo durante travessia em andamento.',
    trafficSafetyRisk: 'Redução do tempo de travessia para pedestres abaixo do limiar mínimo regulamentar.',
    contranStandardViolated: 'Item 4.3 do Volume V do Manual Brasileiro de Sinalização de Trânsito (Tempo de Pedestre Mínimo).',
    correctiveGuardrail: 'Trava rígida de segurança impôs o tempo mínimo inviolável de 18 segundos de travessia (velocidade de 1,0 m/s).',
    finalState: 'PARÂMETRO RETIFICADO',
  },
  {
    id: 'INT-SEG-03',
    timeRecorded: '18:31:10',
    junction: 'Rua da Consolação x Av. Paulista',
    equipmentId: 'DET-SP-CONSOLACAO-04',
    irregularityDetected: 'Atraso na liberação da fila transversal em virtude de refluxo de veículos bloqueando a interseção.',
    trafficSafetyRisk: 'Fechamento de cruzamento e infração do Art. 182 do Código de Trânsito Brasileiro.',
    contranStandardViolated: 'Art. 80 do CTB e Diretrizes de Coordenação Semafórica.',
    correctiveGuardrail: 'Extensão temporária do tempo de vermelho de limpeza (All-Red) de 2,0s para 3,5s para desobstrução da caixa do cruzamento.',
    finalState: 'OPERANDO EM SEGURANÇA',
  },
];

export const MOCK_ATTRIBUTIONS: TrafficAttributionItem[] = [
  {
    parameterName: 'Grau de Saturação da Aproximação Sul (Av. Paulista x Augusta)',
    junctionLocation: 'Av. Paulista x Rua Augusta',
    detectorId: 'DET-SP-PAULISTA-01',
    causalWeightPercent: 42.5,
    gradientDirection: 'Positiva (+)',
    trafficImpactAnalysis: 'Fator preponderante no acúmulo de fila veicular e necessidade de extensão do tempo de verde.',
  },
  {
    parameterName: 'Taxa de Ocupação e Propagação de Fila (Av. Rebouças)',
    junctionLocation: 'Av. Rebouças x Av. Brasil',
    detectorId: 'RAD-SP-REBOUCAS-03',
    causalWeightPercent: 26.8,
    gradientDirection: 'Positiva (+)',
    trafficImpactAnalysis: 'Demanda de escoamento contínuo para evitar bloqueio da caixa de cruzamento a montante.',
  },
  {
    parameterName: 'Capacidade Ociosa na Aproximação Transversal (Alameda Santos)',
    junctionLocation: 'Rua Augusta x Alameda Santos',
    detectorId: 'DET-SP-AUGUSTA-02',
    causalWeightPercent: 18.4,
    gradientDirection: 'Negativa (-)',
    trafficImpactAnalysis: 'Grau de saturação reduzido (x = 0,48) autorizando remanejamento do tempo de ciclo a favor do eixo principal.',
  },
  {
    parameterName: 'Velocidade Média Espacial no Corredor de Escoamento',
    junctionLocation: 'Rua da Consolação x Av. Paulista',
    detectorId: 'DET-SP-CONSOLACAO-04',
    causalWeightPercent: 12.3,
    gradientDirection: 'Positiva (+)',
    trafficImpactAnalysis: 'Velocidade reduzida para 14,0 km/h indicando dissipação lenta da cauda da fila.',
  },
];

export const MOCK_QUESITOS: PeritialQuesitoItem[] = [
  {
    number: 1,
    question: 'Os equipamentos de detecção veicular e controladores semafóricos da malha encontram-se aferidos e operando regularmente segundo normas do INMETRO?',
    answer: 'SIM',
    technicalJustification:
      'A fiscalização dos registros metrológicos comprovou que todos os laços indutivos, radares Doppler e controladores ATU possuem laudos válidos de calibração, operando com índice de disponibilidade de 98,4% e sem falhas de hardware no período auditado.',
  },
  {
    number: 2,
    question: 'A intervenção do sistema adaptativo violou qualquer tempo mínimo de segurança viária estabelecido pelas resoluções do CONTRAN (tempo de amarelo, vermelho geral ou tempo de pedestres)?',
    answer: 'NÃO',
    technicalJustification:
      'Todos os tempos de transição atenderam rigorosamente às normas: tempo de amarelo mantido fixo em 4,0s (superior ao tempo cinemático de 3,32s de Gazis), vermelho de limpeza em 2,0s e tempo de pedestre blindado em 18,0s, correspondendo à velocidade de travessia de 1,0 m/s para acessibilidade universal (NBR 9050).',
  },
  {
    number: 3,
    question: 'Houve registro de anomalias operacionais ou tentativas de reprogramação inadequada que tenham exigido atuação corretiva?',
    answer: 'SIM',
    technicalJustification:
      'Foram registradas 3 intervenções de segurança (uma leitura espúria de radar, uma tentativa de corte precoce de fase e um refluxo de caixa de cruzamento). Em todos os casos, as travas de segurança regulamentares atuaram imediatamente, impedindo a ocorrência de situações de risco aos usuários da via.',
  },
  {
    number: 4,
    question: 'A reprogramação dinâmica semafórica foi eficaz para mitigar a retenção e reduzir o atraso total de viagem no corredor auditado?',
    answer: 'SIM',
    technicalJustification:
      'A extensão do tempo de verde principal combinada com a sincronização de defasagem aumentou a capacidade de escoamento em 22,4%, reduzindo a densidade de saturação de 89,2% para 67,8% em 4 ciclos subsequentes e evitando o travamento das interseções transversais.',
  },
  {
    number: 5,
    question: 'A decisão técnica de alteração de tempos semafóricos encontra-se formalmente motivada e fundamentada em variáveis de tráfego auditáveis?',
    answer: 'SIM',
    technicalJustification:
      'O ato decisório automatizado apoia-se em memorial de cálculo de engenharia de tráfego (Teoria de Filas de Webster, Método do Highway Capacity Manual e Conservação Hidrodinâmica de Lighthill-Whitham-Richards), satisfazendo a exigência de motivação dos atos administrativos (Art. 50 da Lei Federal nº 9.784/1999) e de transparência (Art. 20 da Lei Federal nº 13.709/2018).',
  },
];

export const MOCK_LEGAL_FRAMING: LegalFramingItem[] = [
  {
    article: 'Art. 1º, § 2º da Lei Federal nº 9.503/1997 (Código de Trânsito Brasileiro - CTB)',
    desc: 'Estabelece que o trânsito em condições seguras é um direito de todos e dever dos órgãos e entidades componentes do Sistema Nacional de Trânsito.',
  },
  {
    article: 'Art. 24, Incisos II e III da Lei Federal nº 9.503/1997 (CTB)',
    desc: 'Atribui expressamente ao órgão executivo municipal de trânsito a competência para planejar, projetar, regulamentar e operar o trânsito de veículos e pedestres (inciso II), bem como implantar, manter e operar o sistema de sinalização, os dispositivos e os equipamentos de controle viário (inciso III).',
  },
  {
    article: 'Art. 80 da Lei Federal nº 9.503/1997 (CTB)',
    desc: 'Regulamenta a obrigatoriedade da sinalização de trânsito e respalda a utilização de sistemas semafóricos inteligentes adaptativos e coordenados.',
  },
  {
    article: 'Resolução CONTRAN nº 995/2023 e Manual Brasileiro de Sinalização de Trânsito (Volume V)',
    desc: 'Fixa os critérios técnicos obrigatórios para dimensionamento de fases, tempos de ciclo, tempos de amarelo, vermelho de limpeza e tempos de travessia para pedestres.',
  },
  {
    article: 'Art. 50 da Lei Federal nº 9.784/1999 (Processo Administrativo)',
    desc: 'Exige a motivação explícita, clara e congruente de todos os atos administrativos, inclusive aqueles apoiados em processamento automatizado de dados.',
  },
  {
    article: 'Art. 20 da Lei Federal nº 13.709/2018 (Lei Geral de Proteção de Dados - LGPD)',
    desc: 'Assegura a auditoria, a explicabilidade técnica e a revisão dos critérios utilizados em decisões automatizadas tomadas na administração pública.',
  },
];

export const MOCK_REFERENCES: string[] = [
  'ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. ABNT NBR 13752: Perícias de engenharia na construção civil e sistemas. Rio de Janeiro: ABNT, 1996.',
  'ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. ABNT NBR 10719: Informação e documentação — Relatório técnico e/ou científico — Apresentação. Rio de Janeiro: ABNT, 2015.',
  'ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. ABNT NBR 14724: Informação e documentação — Trabalhos acadêmicos e relatórios — Apresentação. Rio de Janeiro: ABNT, 2011.',
  'BRASIL. Lei Federal nº 9.503, de 23 de setembro de 1997. Institui o Código de Trânsito Brasileiro (CTB - Competência Municipal do Art. 24). Diário Oficial da União: Brasília, DF, 24 set. 1997.',
  'CONSELHO NACIONAL DE TRÂNSITO (CONTRAN). Manual Brasileiro de Sinalização de Trânsito: Volume V — Sinalização Semafórica. Brasília: Ministério dos Transportes, 2022.',
  'GAZIS, D.; HERMAN, R.; MARADUDIN, A. The problem of the amber signal light in traffic flow. Operations Research, v. 8, n. 1, p. 112-132, 1960.',
  'LIGHTHILL, M. J.; WHITHAM, G. B. On kinematic waves. II. A theory of traffic flow on long crowded roads. Proceedings of the Royal Society of London. Series A, v. 229, n. 1178, p. 317-345, 1955.',
  'TRANSPORTATION RESEARCH BOARD (TRB). Highway Capacity Manual (HCM 7th Edition): A Guide for Multimodal Mobility Analysis. Washington, D.C.: National Academies of Sciences, Engineering, and Medicine, 2022.',
  'WEBSTER, F. V. Traffic Signal Settings. Road Research Technical Paper No. 39. London: Her Majesty’s Stationery Office (HMSO), 1958.',
];
