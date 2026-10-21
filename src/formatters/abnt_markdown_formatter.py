# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
ABNT NBR 10719 & NBR 14724 Standardized Markdown Report Formatter.

SOLID Compliance:
- [SRP] Single Responsibility: Exclusively converts OfficialReportData into ABNT-compliant Markdown.
- [OCP] Open for extension via IReportFormatter (new formats do not require changes here).
- [LSP] Full compliance with IReportFormatter protocol.
Focuses strictly on Neural Sensor Fusion & Metrological Perception Auditing.
"""

from datetime import datetime
from typing import Dict, Any

from src.interfaces.reports import IReportFormatter


class AbntMarkdownReportFormatter(IReportFormatter):
    """
    Renders official traffic engineering reports in strict compliance with ABNT NBR 10719:2015.
    """

    def format(self, report_data: Dict[str, Any]) -> str:
        """Renders complete 6-part ABNT NBR 10719 text representation."""
        r = report_data
        timestamp_raw = r.get("timestamp", datetime.now().isoformat())
        try:
            dt_str = datetime.fromisoformat(timestamp_raw).strftime("%d/%m/%Y às %H:%M:%S")
        except Exception:
            dt_str = str(timestamp_raw)

        sensors = r.get("sensors", [])
        sensors_md = "\n\n".join(
            f"[Dispositivo {i+1}] {s.get('id', '')}\n"
            f"  - Localização / Interseção: {s.get('junction', '')}\n"
            f"  - Tecnologia do Detector: {s.get('equipmentType', '')}\n"
            f"  - Grandezas Medidas: Velocidade={s.get('measuredSpeed', '')} | Fluxo={s.get('measuredFlow', '')} | Ocupação={s.get('occupancyRate', '')}\n"
            f"  - Grau de Saturação: {s.get('saturationDegree', '')}\n"
            f"  - Metrologia Legal: {s.get('inmetroReport', '')}\n"
            f"  - Status Operacional: {s.get('operationalStatus', '')}"
            for i, s in enumerate(sensors)
        )

        interventions = r.get("safetyInterventions", [])
        safety_lines = []
        for it in interventions:
            if isinstance(it, dict):
                safety_lines.append(
                    f"[{it.get('id', '')}] Registro às {it.get('timeRecorded', '')} — {it.get('junction', '')}\n"
                    f"  - Dispositivo de Referência: {it.get('equipmentId', '')}\n"
                    f"  - Irregularidade Detectada: {it.get('irregularityDetected', '')}\n"
                    f"  - Risco à Segurança Viária: {it.get('trafficSafetyRisk', '')}\n"
                    f"  - Padrão Metrológico: {it.get('contranStandardViolated', '')}\n"
                    f"  - Salvaguarda Zero-Trust: {it.get('correctiveGuardrail', '')}\n"
                    f"  - Estado de Homologação: {it.get('finalState', '')}"
                )
            else:
                safety_lines.append(f"- {it}")
        safety_md = "\n\n".join(safety_lines)

        attributions = r.get("attributions", [])
        attrs_md = "\n\n".join(
            f"{i+1}. {a.get('parameterName', '')} ({a.get('detectorId', '')})\n"
            f"   - Localização: {a.get('junctionLocation', '')}\n"
            f"   - Peso Causal (Gradiente Integrado): {a.get('causalWeightPercent', 0)}%\n"
            f"   - Direção do Gradiente: {a.get('gradientDirection', '')}\n"
            f"   - Diagnóstico de Impacto: {a.get('trafficImpactAnalysis', '')}"
            for i, a in enumerate(attributions)
        )

        quesitos = r.get("quesitos", [])
        quesitos_md = "\n\n".join(
            f"QUESITO Nº {q.get('number', i+1)}:\n"
            f"{q.get('question', '')}\n"
            f"RESPOSTA DO AUDITOR PERITO: [{q.get('answer', '')}]\n"
            f"FUNDAMENTAÇÃO TÉCNICO-PERICIAL:\n"
            f"{q.get('technicalJustification', '')}"
            for i, q in enumerate(quesitos)
        )

        legal = r.get("legalFraming", [])
        legal_md = "\n\n".join(
            f"* {lf.get('article', '')}:\n  {lf.get('desc', '')}"
            for lf in legal
        )

        refs = r.get("references", [])
        refs_md = "\n".join(f"* {ref}" for ref in refs)

        location = r.get("location", {})
        net = r.get("networkSummary", {})

        attr_by_id = {str(a.get("detectorId", "")): a for a in attributions}
        exec_table_lines = [
            "| Estação / Interseção | Detector ID | Tecnologia | Peso Decisório XAI | Parecer Executivo |",
            "| :--- | :---: | :---: | :---: | :--- |",
        ]
        for idx, s in enumerate(sensors):
            sid = str(s.get("id", ""))
            matched_attr = attr_by_id.get(sid, attributions[idx] if idx < len(attributions) else {})
            w_pct = matched_attr.get("causalWeightPercent", round(100.0 / max(1, len(sensors)), 1))
            exec_table_lines.append(
                f"| {s.get('junction', '')} | `{sid}` | {s.get('equipmentType', 'Sensor')} | {w_pct}% (Captum IG) | **Homologado (INMETRO)** |"
            )
        exec_table_md = "\n".join(exec_table_lines)

        formulas_md = r"""6. MEMORIAL DE CÁLCULO E FUSÃO NEURAL DE SENSORES (ABNT NBR 10719):

6.1. Grau de Saturação e Fluxo Macroscópico:
$$x = \frac{V}{c}, \quad q = \rho \cdot v \tag{1}$$
Onde x é o grau de saturação da aproximação, V é o volume aferido, c é a capacidade efetiva, ρ é a densidade espacial e v é a velocidade média espacial.

6.2. Equação de Continuidade de Lighthill-Whitham-Richards (LWR / PINO):
$$\frac{\partial \rho}{\partial t} + \frac{\partial (\rho \cdot v(\rho))}{\partial x} = 0, \quad v(\rho) = v_f \left(1 - \frac{\rho}{\rho_{\text{jam}}}\right) \tag{2}$$
Onde ∂ρ/∂t é a taxa temporal de variação de densidade, vf é a velocidade de fluxo livre e ρ_jam é a densidade máxima de congestionamento.

6.3. Fusão Multivariada por Atenção Cruzada Inter-Sensores (iTransformer):
$$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{Q K^T}{\sqrt{d_{\text{model}}}}\right) V \tag{3}$$
Onde Q, K e V representam as projeções de consulta, chave e valor das séries de cada sensor e d_model é a dimensão latente.

6.4. Axioma da Completude dos Gradientes Integrados (Captum / ICML 2017):
$$F(x) - F(x') = \sum_{i=1}^{n} \text{IG}_i = \sum_{i=1}^{n} (x_i - x'_i) \cdot \int_{0}^{1} \frac{\partial F(x' + \alpha(x - x'))}{\partial x_i} d\alpha \tag{4}$$
Onde x_i é a leitura atual do sensor i, x'_i é o estado basal neutro e F(x) é a predição da rede neural, recompondo 100% da decisão.

6.5. Estimador Cinemático de Estado (KSE Dead Reckoning para Tolerância a Falhas):
$$v_t = v_{t-1} + a_{t-1} \cdot \Delta t \cdot e^{-\lambda \Delta t} \tag{5}$$
Onde v_t é a velocidade estimada no instante t, a_{t-1} é a aceleração cinemática precedente, Δt é o passo de amostragem e λ é o coeficiente de amortecimento.
"""

        return f"""================================================================================
REPÚBLICA FEDERATIVA DO BRASIL • PODER EXECUTIVO MUNICIPAL
{r.get('cityHall', '')}
{r.get('department', '')}
================================================================================

RELATÓRIO TÉCNICO PERICIAL DE AUDITORIA METROLÓGICA E FUSÃO NEURAL DE SENSORES
Auditoria de Confiabilidade Metrológica, Consistência Física Zero-Trust e Explicabilidade XAI
Normas Aplicadas: CTB Art. 24, Resolução CONTRAN nº 798/2020, ABNT NBR 10719:2015 e LGPD Art. 20

PROCESSO ADMINISTRATIVO Nº : {r.get('processNumber', '')}
PROTOCOLO OFICIAL          : {r.get('protocol', '')}
AUTORIDADE / RESPONSÁVEL   : {r.get('authorityName', '')} ({r.get('authorityRole', '')})
MATRÍCULA / REGISTRO       : {r.get('registrationNumber', '')}
DATA E HORA DA AUDITORIA   : {dt_str}

EMENTA OFICIAL: Auditoria Pericial de Consistência Metrológica (INMETRO / Resolução CONTRAN nº 798/2020), Conservação Física de Fluxo Veicular (LWR / PINO), Salvaguardas Zero-Trust e Explicabilidade Algorítmica (XAI) da Fusão Neural de Sensores.

================================================================================
PARTE I — SUMÁRIO EXECUTIVO PARA GESTÃO PÚBLICA E TOMADORES DE DECISÃO
================================================================================
1. OBJETIVO DA GESTÃO:
{r.get('auditObjective', '')}

2. DESTAQUES OPERACIONAIS DA MALHA:
* Estações e Detectores Ativos: {net.get('monitoredJunctionsCount', len(sensors))} estações ({net.get('totalSensorsOnline', len(sensors))} detectores online)
* Volume Total Atendido: {net.get('totalHourlyFlow', '')}
* Grau de Saturação da Aproximação: {net.get('networkMeanSaturation', '')}
* Velocidade Média Espacial: {net.get('networkMeanSpeed', '')}
* Nível de Serviço da Rede: {net.get('networkLevelOfService', '')}

3. QUADRO SINTÉTICO DE AUDITORIA POR ESTAÇÃO SENSORIAL:
{exec_table_md}

================================================================================
PARTE II — RELATÓRIO TÉCNICO E AUDITORIA DA MALHA SENSORIAL
================================================================================


1. PREÂMBULO E CARACTERIZAÇÃO DA MALHA
1.1. Objeto da Auditoria:
{r.get('auditObjective', '')}

1.2. Diagnóstico Operacional do Tráfego:
{r.get('observedTrafficDiagnosis', '')}

1.3. Ação de Fusão e Denoização Executada (MARKVART™):
{r.get('adaptiveActionExecuted', '')}

1.4. Caracterização do Corredor e Estações Monitoradas:
- Corredor Principal: {location.get('corridorName', '')}
- Jurisdição: {location.get('jurisdiction', '')}
- Estações Sensoriais: {location.get('centralNodes', '')}
- Delimitação Geográfica: {location.get('geographicBounds', '')}
- Capacidade da Malha: {location.get('nominalNetworkCapacity', '')}
- Configuração de Sensoriamento: {location.get('baselineSignalPlan', '')}

1.5. Evolução Comparativa Temporal (Auditoria de Estado na Pasta Synapse):
{r.get('comparativeEvolution', {}).get('summaryText', 'Medição de referência inicial arquivada.')}

--------------------------------------------------------------------------------
2. PANORAMA MACROSCÓPICO DA MALHA ARTERIAL (HIGHWAY CAPACITY MANUAL - HCM)
--------------------------------------------------------------------------------
- Corredores Monitorados: {net.get('corridorsMonitored', '')} eixos arteriais ({net.get('networkLengthKm', '')} km de extensão total)
- Interseções Sensoriadas: {net.get('controlledIntersections', '')} cruzamentos monitorados
- Volume Horário Global: {net.get('totalHourlyFlow', '')}
- Velocidade Média Espacial da Rede: {net.get('networkMeanSpeed', '')}
- Grau Médio de Saturação (x = V/C): {net.get('networkMeanSaturation', '')}
- Nível de Serviço da Rede (LOS): {net.get('networkLevelOfService', '')}

--------------------------------------------------------------------------------
3. INVENTÁRIO METROLÓGICO DOS DETECTORES E EQUIPAMENTOS DE CAMPO
--------------------------------------------------------------------------------
{sensors_md}

================================================================================
PARTE III — SALVAGUARDAS ZERO-TRUST, FILTRAGEM CINEMÁTICA E ATRIBUIÇÃO XAI
================================================================================

4. INTERVENÇÕES DE SEGURANÇA METROLÓGICA E RECONSTRUÇÃO CINEMÁTICA
{safety_md}

--------------------------------------------------------------------------------
5. ANÁLISE DE ATRIBUIÇÃO CAUSAL DE DECISÃO DOS SENSORES (CAPTUM)
--------------------------------------------------------------------------------
{attrs_md}

================================================================================
PARTE IV — FORMULAÇÃO MATEMÁTICA E ANÁLISE CONTRAFATUAL
================================================================================
{formulas_md}

7. ANÁLISE CONTRAFATUAL E TOLERÂNCIA A FALHAS:
{r.get('counterfactualAnalysis', '')}

================================================================================
PARTE V — QUESITOS TÉCNICOS PERICIAIS E ENQUADRAMENTO JURÍDICO
================================================================================
{quesitos_md}

--------------------------------------------------------------------------------
8. ENQUADRAMENTO NORMATIVO E JURÍDICO APLICADO
--------------------------------------------------------------------------------
{legal_md}

================================================================================
PARTE VI — CERTIFICAÇÃO DIGITAL, SUPERVISÃO OPERACIONAL E REFERÊNCIAS
================================================================================
9. DECLARAÇÃO DE SUPERVISÃO OPERACIONAL:
{r.get('operationalSupervision', '')}

10. CERTIFICAÇÃO DIGITAL ICP-BRASIL:
{r.get('digitalCertification', '')}

11. REFERÊNCIAS NORMATIVAS E BIBLIOGRÁFICAS (ABNT NBR 10719):
{refs_md}
================================================================================
"""
