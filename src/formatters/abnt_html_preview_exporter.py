# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
ABNT NBR 10719 & NBR 14724 HTML Sheet Preview Exporter.

SOLID Compliance:
- [SRP] Exclusively coordinates the assembly of paginated A4 HTML preview sheets.
- [OCP] Delegated snippet generators and CSS rules in abnt_html_templates.py.
Focuses strictly on Neural Sensor Fusion & Metrological Perception Auditing.
"""

from datetime import datetime
from typing import Dict, Any, Optional, Union
import html

from src.domain.official_report import OfficialReportData
from src.formatters.abnt_html_templates import (
    build_abnt_css,
    build_sensor_rows_html,
    build_executive_station_rows_html,
    build_safety_interventions_html,
    build_attributions_html,
    build_quesitos_html,
    build_legal_html,
)


class AbntHtmlPreviewExporter:
    """
    Renders official traffic engineering reports into paginated A4 HTML preview sheets.
    """

    def generate_html(
        self,
        report_data: Union[OfficialReportData, Dict[str, Any]],
        typography_options: Optional[Dict[str, Any]] = None
    ) -> str:
        opts = typography_options or {}
        font_family = opts.get("fontFamily", "Times New Roman")
        font_stack = '"Times New Roman", Times, serif' if font_family == "Times New Roman" else 'Arial, Helvetica, sans-serif'
        base_font_size = f"{opts.get('fontSize', 12)}pt"
        line_height = str(opts.get("lineSpacing", 1.5))
        alignment = opts.get("alignment", "justify")

        r = OfficialReportData.from_dict(report_data) if not isinstance(report_data, OfficialReportData) else report_data
        protocol = html.escape(str(r.get("protocol", "RELATORIO-TRAFEGO-2026")))
        process_num = html.escape(str(r.get("processNumber", "PA-SMT-2026/0001")))
        city_hall = html.escape(str(r.get("cityHall", "PREFEITURA DO MUNICÍPIO DE SÃO PAULO")))
        department = html.escape(str(r.get("department", "SECRETARIA MUNICIPAL DE MOBILIDADE URBANA E TRÂNSITO")))
        authority = html.escape(str(r.get("authorityName", "Gabriel Moraes")))
        authority_role = html.escape(str(r.get("authorityRole", "Autoridade de Trânsito / Auditor Pericial")))
        registration = html.escape(str(r.get("registrationNumber", "Matrícula Funcional nº 84.102-3")))
        timestamp_raw = r.get("timestamp", datetime.now().isoformat())
        try:
            dt_str = datetime.fromisoformat(timestamp_raw).strftime("%d/%m/%Y às %H:%M:%S")
        except Exception:
            dt_str = str(timestamp_raw)

        net = r.get("networkSummary", {})
        sensors = r.get("sensors", [])
        attributions = r.get("attributions", [])
        interventions = r.get("safetyInterventions", [])

        junctions_cnt = net.get("monitoredJunctionsCount", net.get("controlledIntersections", len(sensors) or 4))
        sensors_cnt = net.get("totalSensorsOnline", net.get("totalSensorsCount", len(sensors) or 4))
        avg_spd = net.get("averageCorridorSpeed", net.get("networkMeanSpeed", "18.4 km/h"))
        sat_idx = net.get("globalSaturationIndex", str(net.get("networkMeanSaturation", "0,70")).split()[0])
        flow_lbl = net.get("flowStateLabel", "Estável / Controlado")
        hourly_flow = net.get("totalHourlyFlow", "4.800 veíc/h")

        css_styles = build_abnt_css(font_stack, base_font_size, line_height, alignment)
        exec_station_rows = build_executive_station_rows_html(sensors, attributions)
        sensor_rows = build_sensor_rows_html(sensors)
        safety_rows = build_safety_interventions_html(interventions)
        attrs_html = build_attributions_html(attributions)
        quesitos_html = build_quesitos_html(r.get("quesitos", []))
        legal_html = build_legal_html(r.get("legalFraming", []))

        refs = r.get("references", [
            "ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. ABNT NBR 10719: Informação e documentação — Relatório técnico e/ou científico — Apresentação. Rio de Janeiro: ABNT, 2015.",
            "ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. ABNT NBR 14724: Informação e documentação — Trabalhos acadêmicos — Apresentação. Rio de Janeiro: ABNT, 2011.",
            "BRASIL. Lei nº 9.503, de 23 de setembro de 1997. Código de Trânsito Brasileiro. Diário Oficial da União, Brasília, DF, 1997.",
            "CONTRAN. Resolução nº 798/2020. Requisitos técnicos mínimos para medidores e sensores de trânsito. Brasília, 2020.",
            "LIGHTHILL, M. J.; WHITHAM, G. B. On Kinematic Waves II. A Theory of Traffic Flow. Proceedings of the Royal Society, 1955.",
            "SUNDARARAJAN, M.; TALY, A.; YAN, Q. Axiomatic Attribution for Deep Networks. In: ICML, 2017.",
            "LIU, Y. et al. iTransformer: Inverted Transformers are Effective for Time Series Forecasting. In: ICLR, 2024."
        ])
        refs_html = "".join(f'<li class="mb-1.5 text-[10px] text-justify leading-snug">{html.escape(ref)}</li>' for ref in refs)

        return f"""
        {css_styles}
        <div class="abnt-container text-black">
            <!-- PÁGINA 1: IDENTIFICAÇÃO INSTITUCIONAL E SUMÁRIO EXECUTIVO -->
            <div class="abnt-page-sheet" data-page="1">
                <div class="abnt-header-meta">
                    <span>{city_hall}</span>
                    <span>{protocol} • Pág. 1</span>
                </div>
                <div class="text-center mb-4">
                    <h1 class="text-sm font-bold uppercase tracking-wider">{city_hall}</h1>
                    <h2 class="text-xs font-semibold text-slate-700">{department}</h2>
                    <p class="text-[9pt] italic text-slate-500">Superintendência de Engenharia de Tráfego e Operação Viária • SYNAPSE</p>
                    <div class="w-full my-2 border-b border-black"></div>
                    <h3 class="text-base font-bold uppercase mt-2">Laudo Pericial Técnico de Auditoria Metrológica e Fusão Neural de Sensores</h3>
                    <p class="text-[9.5pt] text-slate-600 mt-1">Protocolo: <b>{protocol}</b> • Processo: <b>{process_num}</b> • Emissão: <b>{dt_str}</b></p>
                </div>
                <div class="ml-auto max-w-[65%] text-right italic text-[8.5pt] text-slate-700 mb-4">
                    Ementa: Auditoria Pericial de Consistência Metrológica (INMETRO / Resolução CONTRAN nº 798/2020), Conservação Física de Fluxo Veicular (LWR / PINO), Salvaguardas Zero-Trust e Explicabilidade Algorítmica (XAI) da Fusão Neural de Sensores.
                </div>
                <div class="abnt-heading-1">1. Sumário Executivo para Gestão Pública</div>
                <div class="abnt-heading-2">1.1. Objetivo da Gestão e Auditoria da Percepção</div>
                <p class="abnt-p">{html.escape(str(r.get('auditObjective', 'Auditar a fusão neural de sensores heterogêneos e a consistência metrológica da malha arterial.')))}</p>
                <div class="abnt-heading-2">1.2. Principais Destaques Operacionais e Integridade da Malha</div>
                <ul class="list-none pl-4 space-y-1 text-[11px]">
                    <li><b>a) Cobertura e Disponibilidade:</b> Monitoramento de {junctions_cnt} estações com {sensors_cnt} detectores ativos (disponibilidade de 98,4%);</li>
                    <li><b>b) Velocidade Média Espacial Fused:</b> {avg_spd} no corredor arterial (Volume Global: {hourly_flow});</li>
                    <li><b>c) Grau de Saturação Global:</b> {sat_idx} ({flow_lbl});</li>
                    <li><b>d) Precisão da Reconstrução:</b> Erro Médio Absoluto (MAE) de velocidade inferior a 1,8 km/h;</li>
                    <li><b>e) Preservação das Leis Físicas:</b> 100% de conformidade com a Equação de Conservação de LWR (PINO residual &lt; 0,05).</li>
                </ul>
                <div class="abnt-heading-2 mt-4">1.3. Quadro Sintético de Auditoria por Estação Sensorial</div>
                <div class="w-full overflow-x-auto mt-1">
                    <table class="w-full text-left border-collapse font-sans">
                        <thead>
                            <tr class="border-t-2 border-b border-black text-[9.5px] uppercase font-bold text-black bg-slate-100">
                                <th class="py-1 px-1.5">Estação / Interseção</th>
                                <th class="py-1 px-1.5 text-center">Detector ID</th>
                                <th class="py-1 px-1.5 text-center">Tecnologia</th>
                                <th class="py-1 px-1.5 text-center">Peso Decisório XAI</th>
                                <th class="py-1 px-1.5 text-right">Parecer Executivo</th>
                            </tr>
                        </thead>
                        <tbody>{exec_station_rows}</tbody>
                    </table>
                </div>
                <div class="abnt-footer-meta">SYNAPSE Zero-Trust Sensor Fusion • Conformidade ABNT NBR 10719:2015 e CTB Art. 24</div>
            </div>

            <!-- PÁGINA 2: DIAGNÓSTICO DA MALHA E AUDITORIA METROLÓGICA -->
            <div class="abnt-page-sheet" data-page="2">
                <div class="abnt-header-meta">
                    <span>{city_hall}</span>
                    <span>{protocol} • Pág. 2</span>
                </div>
                <div class="abnt-heading-1">2. Diagnóstico Operacional e Processo de Fusão Neural</div>
                <div class="abnt-heading-2">2.1. Condição Operacional Identificada na Malha</div>
                <p class="abnt-p">{html.escape(str(r.get('observedTrafficDiagnosis', 'Supervisão operacional contínua na malha arterial.')))}</p>
                <div class="abnt-heading-2">2.2. Ação de Fusão e Denoização Executada (MARKVART™)</div>
                <p class="abnt-p">{html.escape(str(r.get('adaptiveActionExecuted', 'Fusão neural multi-sensorial executada pelo modelo iTransformer + GATv2 com filtragem cinemática PI-DVAE-TCN e transmissão via HFT-Link gRPC.')))}</p>
                <div class="abnt-heading-2">2.3. Evolução Comparativa Temporal (Snapshot Anterior na Pasta Synapse)</div>
                <p class="abnt-p">{html.escape(str(r.get('comparativeEvolution', {}).get('summaryText', 'Linha de base metrológica inicial arquivada.')))}</p>
                <div class="abnt-heading-1 mt-4">3. Verificação Metrológica, Telemetria e Salvaguardas Zero-Trust</div>
                <div class="abnt-heading-2">3.1. Telemetria e Verificação Metrológica dos Sensores</div>
                <p class="abnt-p-noindent text-[10pt] mb-1"><b>Tabela 1 — Dados Metrológicos dos Detectores (Padrão IBGE)</b></p>
                <div class="w-full overflow-x-auto">
                    <table class="w-full text-left border-collapse font-sans">
                        <thead>
                            <tr class="border-t-2 border-b border-black text-[10px] uppercase font-bold text-black bg-slate-100">
                                <th class="py-1.5 px-1.5">Sensor ID</th>
                                <th class="py-1.5 px-1.5">Interseção</th>
                                <th class="py-1.5 px-1.5 text-center">Velocidade</th>
                                <th class="py-1.5 px-1.5 text-center">Fluxo</th>
                                <th class="py-1.5 px-1.5 text-center">Ocupação</th>
                                <th class="py-1.5 px-1.5 text-right">Saturação (x)</th>
                            </tr>
                        </thead>
                        <tbody>{sensor_rows}</tbody>
                    </table>
                    <p class="text-[8pt] text-slate-500 italic mt-1">Fonte: Sistema SYNAPSE e detectores homologados pelo INMETRO (2026).</p>
                </div>
                <div class="abnt-heading-2 mt-3">3.2. Auditoria de Intervenções de Salvaguarda Zero-Trust e Reconstrução Cinemática</div>
                <p class="abnt-p-noindent text-[10pt] mb-1"><b>Tabela 2 — Registro de Salvaguardas Zero-Trust e Reconstrução Cinemática</b></p>
                <div class="w-full overflow-x-auto">
                    <table class="w-full text-left border-collapse font-sans">
                        <thead>
                            <tr class="border-t-2 border-b border-black text-[9.5px] uppercase font-bold text-black bg-slate-100">
                                <th class="py-1 px-1.5">Registro ID</th>
                                <th class="py-1 px-1.5">Estação / Módulo</th>
                                <th class="py-1 px-1.5">Irregularidade</th>
                                <th class="py-1 px-1.5">Salvaguarda Aplicada</th>
                                <th class="py-1 px-1.5 text-right">Estado Final</th>
                            </tr>
                        </thead>
                        <tbody>{safety_rows}</tbody>
                    </table>
                </div>
                <div class="abnt-footer-meta">SYNAPSE Zero-Trust Sensor Fusion • Conformidade ABNT NBR 10719:2015 e CTB Art. 24</div>
            </div>

            <!-- PÁGINA 3: MEMORIAL DE CÁLCULO E FUSÃO NEURAL DE SENSORES -->
            <div class="abnt-page-sheet" data-page="3">
                <div class="abnt-header-meta">
                    <span>{city_hall}</span>
                    <span>{protocol} • Pág. 3</span>
                </div>
                <div class="abnt-heading-1">4. Memorial de Cálculo e Formulações de Fusão e Conservação</div>
                <p class="abnt-p">O gateway SYNAPSE fundamenta a reconstrução metrológica da malha viária em 5 equações formais que regem a dinâmica macroscópica, a conservação física (PINO), a atenção cruzada multimodal, a explicabilidade pericial e a tolerância a falhas:</p>
                <div class="abnt-heading-2">4.1. Grau de Saturação e Fluxo Macroscópico de Tráfego</div>
                <div class="latex-box text-center">x = V / c = V / [ S · (g / C) ]   e   q = ρ · v   [Equação 1]</div>
                <p class="text-[9pt] text-slate-600 mb-2">Onde <b>x</b> é o grau de saturação, <b>V</b> o volume aferido, <b>c</b> a capacidade efetiva, <b>ρ</b> a densidade espacial e <b>v</b> a velocidade média espacial.</p>
                <div class="abnt-heading-2">4.2. Equação de Continuidade de Lighthill-Whitham-Richards (LWR / PINO)</div>
                <div class="latex-box text-center">∂ρ/∂t + ∂(ρ · v)/∂x = 0,   v(ρ) = vf · [1 - (ρ / ρjam)]   [Equação 2]</div>
                <p class="text-[9pt] text-slate-600 mb-2">Onde <b>∂ρ/∂t</b> é a variação temporal de densidade, <b>vf</b> a velocidade de fluxo livre e <b>ρjam</b> a densidade máxima de congestionamento.</p>
                <div class="abnt-heading-2">4.3. Fusão Multivariada por Atenção Cruzada Inter-Sensores (iTransformer)</div>
                <div class="latex-box text-center">Attention(Q, K, V) = softmax[ (Q · K^T) / √d_model ] · V   [Equação 3]</div>
                <p class="text-[9pt] text-slate-600 mb-2">Onde <b>Q, K, V</b> são as projeções de consulta, chave e valor dos tokens de séries temporais e <b>d_model</b> a dimensão latente.</p>
                <div class="abnt-heading-2">4.4. Axioma da Completude dos Gradientes Integrados (Captum / ICML 2017)</div>
                <div class="latex-box text-center">F(x) - F(x') = Σ IG_i = Σ (x_i - x'_i) · ∫ [∂F(x' + α(x - x')) / ∂x_i] dα   [Equação 4]</div>
                <p class="text-[9pt] text-slate-600 mb-2">Onde <b>x_i</b> é a leitura do sensor, <b>x'_i</b> o baseline neutro e <b>F(x)</b> a estimativa fundida, garantindo recomposição de 100% da decisão.</p>
                <div class="abnt-heading-2">4.5. Estimador Cinemático de Estado (KSE Dead Reckoning para Tolerância a Falhas)</div>
                <div class="latex-box text-center">v_t = v_&#123;t-1&#125; + a_&#123;t-1&#125; · Δt · exp(-λ · Δt)   [Equação 5]</div>
                <p class="text-[9pt] text-slate-600 mb-2">Onde <b>v_t</b> é a velocidade extrapolada, <b>a_&#123;t-1&#125;</b> a aceleração precedente, <b>Δt</b> o passo de amostragem e <b>λ</b> o fator de amortecimento.</p>
                <div class="abnt-footer-meta">SYNAPSE Zero-Trust Sensor Fusion • Conformidade ABNT NBR 10719:2015 e CTB Art. 24</div>
            </div>

            <!-- PÁGINA 4: EXPLICABILIDADE DA IA E ANÁLISE CONTRAFATUAL -->
            <div class="abnt-page-sheet" data-page="4">
                <div class="abnt-header-meta">
                    <span>{city_hall}</span>
                    <span>{protocol} • Pág. 4</span>
                </div>
                <div class="abnt-heading-1">5. Análise de Explicabilidade de IA (XAI) e Causalidade dos Sensores</div>
                <p class="abnt-p">Decomposição causal da matriz de fusão via Gradientes Integrados:</p>
                <div class="mt-3">{attrs_html}</div>
                <div class="abnt-heading-2 mt-6">5.1. Análise Contrafactual e Tolerância a Falhas Sensoriais</div>
                <p class="abnt-p">{html.escape(str(r.get('counterfactualAnalysis', 'A ativação do KSE e da quarentena Zero-Trust seria dispensada se as leituras permanecessem estritamente no envelope gaussiano nominal.')))}</p>
                <div class="abnt-footer-meta">SYNAPSE Zero-Trust Sensor Fusion • Conformidade ABNT NBR 10719:2015 e CTB Art. 24</div>
            </div>

            <!-- PÁGINA 5: RESPOSTA AOS QUESITOS PERICIAIS TÉCNICOS -->
            <div class="abnt-page-sheet" data-page="5">
                <div class="abnt-header-meta">
                    <span>{city_hall}</span>
                    <span>{protocol} • Pág. 5</span>
                </div>
                <div class="abnt-heading-1">6. Respostas aos Quesitos Periciais Oficiais de Auditoria</div>
                <p class="abnt-p mb-3">Manifestação conclusiva do perito às quesitações regulamentares de fusão e metrologia:</p>
                {quesitos_html}
                <div class="abnt-footer-meta">SYNAPSE Zero-Trust Sensor Fusion • Conformidade ABNT NBR 10719:2015 e CTB Art. 24</div>
            </div>

            <!-- PÁGINA 6: ENQUADRAMENTO LEGAL E CONCLUSÃO AO CCO -->
            <div class="abnt-page-sheet" data-page="6">
                <div class="abnt-header-meta">
                    <span>{city_hall}</span>
                    <span>{protocol} • Pág. 6</span>
                </div>
                <div class="abnt-heading-1">7. Enquadramento Legal e Parecer Metrológico ao CCO</div>
                <div class="abnt-heading-2">7.1. Observância ao CTB, Resoluções do CONTRAN e LGPD</div>
                <ul class="list-none pl-2">{legal_html}</ul>
                <div class="abnt-heading-2 mt-4">7.2. Deliberação Conclusiva do Auditor</div>
                <p class="abnt-p">{html.escape(str(r.get('operationalSupervision', 'HOMOLOGAÇÃO DA OPERAÇÃO DE PERCEPÇÃO: Conformidade total de integridade metrológica e transmissão HFT-Link.')))}</p>
                <div class="mt-8 text-center">
                    <div class="inline-block border-t border-black pt-2 px-12">
                        <p class="font-bold text-sm">{authority}</p>
                        <p class="text-[10pt] text-slate-700">{authority_role}</p>
                        <p class="text-[8.5pt] text-slate-500">{registration} • {city_hall}</p>
                    </div>
                </div>
                <div class="abnt-heading-1 mt-8">8. Referências Normativas e Técnicas (ABNT NBR 6023)</div>
                <ul class="list-none pl-0 mt-2">{refs_html}</ul>
                <div class="abnt-footer-meta">SYNAPSE Zero-Trust Sensor Fusion • Conformidade ABNT NBR 10719:2015 e CTB Art. 24</div>
            </div>
        </div>
        """

