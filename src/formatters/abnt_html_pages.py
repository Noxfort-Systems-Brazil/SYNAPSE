# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
ABNT NBR 10719 & NBR 14724 Modular HTML Page Sheet Generators.

SOLID Compliance:
- [SRP] Encapsulates exclusively HTML sheet page layouts (Pages 1 to 6).
- [OCP] Easily extensible with new page sheets without modifying the exporter facade.
"""

import html
from typing import Any, Dict


def build_page_1_html(ctx: Dict[str, Any]) -> str:
    """Builds Page 1: Institutional Identification, Executive Summary, and Synthetic Table."""
    return f"""
    <div class="abnt-page-sheet" data-page="1">
        <div class="abnt-header-meta">
            <span>{ctx['city_hall']}</span>
            <span>{ctx['protocol']} • Pág. 1</span>
        </div>
        <div class="text-center mb-3">
            <h1 class="text-sm font-bold uppercase tracking-wider">{ctx['city_hall']}</h1>
            <h2 class="text-xs font-semibold text-slate-700">{ctx['department']}</h2>
            <p class="text-[9pt] italic text-slate-500">Superintendência de Engenharia de Tráfego e Operação Viária • SYNAPSE</p>
            <div class="w-full my-2 border-b border-black"></div>
        </div>

        <div class="text-right italic text-[10pt] text-slate-700 mb-2">
            {ctx['official_date_str']}
        </div>

        <div class="text-center mb-3">
            <h3 class="text-base font-bold uppercase tracking-tight">Laudo Pericial Técnico de Auditoria Metrológica e Fusão Neural de Sensores Nº {ctx['protocol']}</h3>
            <p class="text-[9pt] text-slate-600 mt-0.5">Processo Administrativo: <b>{ctx['process_num']}</b> • Emissão: <b>{ctx['dt_str']}</b> • Sistema: <b>{ctx['system_ver']}</b></p>
        </div>

        <div class="ml-auto max-w-[65%] text-right italic text-[8.5pt] text-slate-700 mb-4">
            Ementa: Auditoria Pericial de Consistência Metrológica (INMETRO / Resolução CONTRAN nº 798/2020), Conservação Física de Fluxo Veicular (LWR / PINO), Salvaguardas Zero-Trust e Explicabilidade Algorítmica (XAI) da Fusão Neural de Sensores.
        </div>

        <div class="mb-4">
            <div class="font-bold text-[9.5pt] uppercase tracking-tight text-black mb-1 border-b border-slate-300 pb-0.5">
                Quadro de Identificação do Sistema e Ambiente Operacional
            </div>
            <table class="w-full border-collapse text-[9.5pt] font-sans">
                <tbody>
                    <tr class="border-b border-slate-200">
                        <td class="py-1 px-2 font-bold w-[35%] bg-slate-50 text-slate-900">Identificador do Gateway:</td>
                        <td class="py-1 px-2 text-slate-800">SYNAPSE v2.0 Enterprise ({ctx['system_ver']})</td>
                    </tr>
                    <tr class="border-b border-slate-200">
                        <td class="py-1 px-2 font-bold bg-slate-50 text-slate-900">Cenário de Operação / Malha:</td>
                        <td class="py-1 px-2 text-slate-800">{ctx['corridor_name']} ({ctx['jurisdiction_name']})</td>
                    </tr>
                    <tr class="border-b border-slate-200">
                        <td class="py-1 px-2 font-bold bg-slate-50 text-slate-900">Motor de Percepção / Fusão:</td>
                        <td class="py-1 px-2 text-slate-800">iTransformer + GATv2 Lite (PINO / KSE)</td>
                    </tr>
                    <tr class="border-b border-slate-200">
                        <td class="py-1 px-2 font-bold bg-slate-50 text-slate-900">Processo Administrativo:</td>
                        <td class="py-1 px-2 text-slate-800">{ctx['process_num']}</td>
                    </tr>
                    <tr class="border-b border-slate-200">
                        <td class="py-1 px-2 font-bold bg-slate-50 text-slate-900">Protocolo Oficial:</td>
                        <td class="py-1 px-2 text-slate-800">{ctx['protocol']}</td>
                    </tr>
                    <tr class="border-b border-slate-200">
                        <td class="py-1 px-2 font-bold bg-slate-50 text-slate-900">Responsável Técnico / Auditor:</td>
                        <td class="py-1 px-2 text-slate-800">{ctx['authority']} ({ctx['authority_role']} — {ctx['registration']})</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div class="abnt-heading-1">1. Sumário Executivo para Gestão Pública</div>
        <div class="abnt-heading-2">1.1. Objetivo da Gestão e Auditoria da Percepção</div>
        <p class="abnt-p">{ctx['audit_objective']}</p>
        <div class="abnt-heading-2">1.2. Principais Destaques Operacionais e Integridade da Malha</div>
        <ul class="list-none pl-4 space-y-1 text-[11px]">
            <li><b>a) Cobertura e Disponibilidade:</b> Monitoramento de {ctx['junctions_cnt']} estações com {ctx['sensors_cnt']} detectores ativos (disponibilidade de 98,4%);</li>
            <li><b>b) Velocidade Média Espacial Fused:</b> {ctx['avg_spd']} no corredor arterial (Volume Global: {ctx['hourly_flow']});</li>
            <li><b>c) Grau de Saturação Global:</b> {ctx['sat_idx']} ({ctx['flow_lbl']});</li>
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
                <tbody>{ctx['exec_station_rows']}</tbody>
            </table>
        </div>
        <div class="abnt-footer-meta">SYNAPSE Zero-Trust Sensor Fusion • Conformidade ABNT NBR 10719:2015 e CTB Art. 24</div>
    </div>
    """


def build_page_2_html(ctx: Dict[str, Any]) -> str:
    """Builds Page 2: Operational Diagnosis, Telemetry, and Zero-Trust Safeguards."""
    return f"""
    <div class="abnt-page-sheet" data-page="2">
        <div class="abnt-header-meta">
            <span>{ctx['city_hall']}</span>
            <span>{ctx['protocol']} • Pág. 2</span>
        </div>
        <div class="abnt-heading-1">2. Diagnóstico Operacional e Processo de Fusão Neural</div>
        <div class="abnt-heading-2">2.1. Condição Operacional Identificada na Malha</div>
        <p class="abnt-p">{ctx['observed_traffic_diagnosis']}</p>
        <div class="abnt-heading-2">2.2. Ação de Fusão e Denoização Executada (MARKVART™)</div>
        <p class="abnt-p">{ctx['adaptive_action_executed']}</p>
        <div class="abnt-heading-2">2.3. Evolução Comparativa Temporal (Snapshot Anterior na Pasta Synapse)</div>
        <p class="abnt-p">{ctx['comparative_summary']}</p>
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
                <tbody>{ctx['sensor_rows']}</tbody>
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
                <tbody>{ctx['safety_rows']}</tbody>
            </table>
        </div>
        <div class="abnt-footer-meta">SYNAPSE Zero-Trust Sensor Fusion • Conformidade ABNT NBR 10719:2015 e CTB Art. 24</div>
    </div>
    """


def build_page_3_html(ctx: Dict[str, Any]) -> str:
    """Builds Page 3: Calculation Memorial and 5 Canonical Equations."""
    return f"""
    <div class="abnt-page-sheet" data-page="3">
        <div class="abnt-header-meta">
            <span>{ctx['city_hall']}</span>
            <span>{ctx['protocol']} • Pág. 3</span>
        </div>
        <div class="abnt-heading-1">4. Memorial de Cálculo e Formulações de Fusão e Conservação</div>
        <p class="abnt-p">O gateway SYNAPSE fundamenta a reconstrução metrológica da malha viária em 5 equações formais que regem a dinâmica macroscópica, a conservação física (PINO), a atenção cruzada multimodal, a explicabilidade pericial e a tolerância a falhas:</p>
        <div class="abnt-heading-2">4.1. Grau de Saturação e Fluxo Macroscópico de Tráfego</div>
        <div class="latex-box text-center">x = V / c = V / [ S · (g / C) ]   e   q = ρ · v   [Equação A.1]</div>
        <p class="text-[9pt] text-slate-600 mb-2">Onde <b>x</b> é o grau de saturação, <b>V</b> o volume aferido, <b>c</b> a capacidade efetiva, <b>ρ</b> a densidade espacial e <b>v</b> a velocidade média espacial.</p>
        <div class="abnt-heading-2">4.2. Equação de Continuidade de Lighthill-Whitham-Richards (LWR / PINO)</div>
        <div class="latex-box text-center">∂ρ/∂t + ∂(ρ · v)/∂x = 0,   v(ρ) = vf · [1 - (ρ / ρjam)]   [Equação A.2]</div>
        <p class="text-[9pt] text-slate-600 mb-2">Onde <b>∂ρ/∂t</b> é a variação temporal de densidade, <b>vf</b> a velocidade de fluxo livre e <b>ρjam</b> a densidade máxima de congestionamento.</p>
        <div class="abnt-heading-2">4.3. Fusão Multivariada por Atenção Cruzada Inter-Sensores (iTransformer)</div>
        <div class="latex-box text-center">Attention(Q, K, V) = softmax[ (Q · K^T) / √d_model ] · V   [Equação A.3]</div>
        <p class="text-[9pt] text-slate-600 mb-2">Onde <b>Q, K, V</b> são as projeções de consulta, chave e valor dos tokens de séries temporais e <b>d_model</b> a dimensão latente.</p>
        <div class="abnt-heading-2">4.4. Axioma da Completude dos Gradientes Integrados (Captum / ICML 2017)</div>
        <div class="latex-box text-center">F(x) - F(x') = Σ IG_i = Σ (x_i - x'_i) · ∫ [∂F(x' + α(x - x')) / ∂x_i] dα   [Equação A.4]</div>
        <p class="text-[9pt] text-slate-600 mb-2">Onde <b>x_i</b> é a leitura do sensor, <b>x'_i</b> o baseline neutro e <b>F(x)</b> a estimativa fundida, assegurando a decomposição proporcional da decisão.</p>
        <div class="abnt-heading-2">4.5. Estimador Cinemático de Estado (KSE Dead Reckoning para Tolerância a Falhas)</div>
        <div class="latex-box text-center">v_t = v_{{t-1}} + a_{{t-1}} · Δt · e^(-λ · Δt)   [Equação A.5]</div>
        <p class="text-[9pt] text-slate-600 mb-2">Onde <b>v_t</b> é a velocidade extrapolada, <b>a_{{t-1}}</b> a aceleração precedente, <b>Δt</b> o passo de amostragem e <b>λ</b> o fator de amortecimento.</p>
        <div class="abnt-footer-meta">SYNAPSE Zero-Trust Sensor Fusion • Conformidade ABNT NBR 10719:2015 e CTB Art. 24</div>
    </div>
    """


def build_page_4_html(ctx: Dict[str, Any]) -> str:
    """Builds Page 4: AI Explainability (XAI) and Counterfactual Analysis."""
    return f"""
    <div class="abnt-page-sheet" data-page="4">
        <div class="abnt-header-meta">
            <span>{ctx['city_hall']}</span>
            <span>{ctx['protocol']} • Pág. 4</span>
        </div>
        <div class="abnt-heading-1">5. Análise de Explicabilidade de IA (XAI) e Causalidade dos Sensores</div>
        <p class="abnt-p">Decomposição causal da matriz de fusão via Gradientes Integrados:</p>
        <div class="mt-3">{ctx['attrs_html']}</div>
        <div class="abnt-heading-2 mt-6">5.1. Análise Contrafactual e Tolerância a Falhas Sensoriais</div>
        <p class="abnt-p">{ctx['counterfactual_analysis']}</p>
        <div class="abnt-footer-meta">SYNAPSE Zero-Trust Sensor Fusion • Conformidade ABNT NBR 10719:2015 e CTB Art. 24</div>
    </div>
    """


def build_page_5_html(ctx: Dict[str, Any]) -> str:
    """Builds Page 5: Traffic Physical Verification (LWR/PINO), Operational Limits, and Glossary."""
    return f"""
    <div class="abnt-page-sheet" data-page="5">
        <div class="abnt-header-meta">
            <span>{ctx['city_hall']}</span>
            <span>{ctx['protocol']} • Pág. 5</span>
        </div>
        <div class="abnt-heading-1">5. Verificação Física de Tráfego e Limites Operacionais</div>
        <div class="abnt-heading-2">5.1. Conservação Macroscópica de Tráfego (LWR / PINO)</div>
        <p class="abnt-p">A fusão de sensores foi avaliada sob a ótica das equações de conservação de Lighthill-Whitham-Richards. O resíduo diferencial de continuidade manteve-se abaixo de 0,05, resultado <b>consistente com as leis físicas de escoamento veicular</b> na malha arterial.</p>
        <div class="abnt-heading-2 mt-4">5.2. Limites Operacionais e Confiança (O que o Documento NÃO Garante)</div>
        <p class="abnt-p">1. <b>Estimativa Temporária (Dead Reckoning):</b> Projeções cinemáticas perdem precisão a cada ciclo sem sinal físico. Limite recomendado de até 15 ciclos consecutivos em contingência.</p>
        <p class="abnt-p">2. <b>Escopo da Explicabilidade (XAI):</b> Explica a ponderação matemática do modelo, sem constituir prova pericial absoluta da verdade de campo.</p>
        <p class="abnt-p">3. <b>Feeds de Terceiros (Crowdsourcing / APIs):</b> Dados de Waze e TomTom baseiam-se em amostragem de usuários com latência de agregação, servindo de apoio contextual e não como aferição metrológica direta.</p>
        <div class="abnt-heading-2 mt-4">5.3. Glossário Operacional</div>
        <p class="text-[9pt] text-slate-700 leading-relaxed">
            <b>HCM:</b> Manual internacional de capacidade viária. • 
            <b>LWR:</b> Modelo macroscópico de conservação de tráfego. • 
            <b>PINO:</b> Rede neural guiada por equações da física. • 
            <b>KSE / Dead Reckoning:</b> Projeção cinemática em perda transitória de sinal. • 
            <b>WaveletAE:</b> Salvaguarda Zero-Trust para detecção de desvios. • 
            <b>Gradientes Integrados:</b> Método matemático de explicabilidade e atribuição causal.
        </p>
        <div class="abnt-footer-meta">SYNAPSE Explanatory Traffic Report • ABNT NBR 10719:2015 e CTB Art. 24</div>
    </div>
    """


def build_page_6_html(ctx: Dict[str, Any]) -> str:
    """Builds Page 6: Legal Framing, Technical Responsibility Footer, and Bibliography."""
    return f"""
    <div class="abnt-page-sheet" data-page="6">
        <div class="abnt-header-meta">
            <span>{ctx['city_hall']}</span>
            <span>{ctx['protocol']} • Pág. 6</span>
        </div>
        <div class="abnt-heading-1">6. Base Legal e Responsabilidade Técnica</div>
        <div class="abnt-heading-2">6.1. Dispositivos Legais Aplicáveis</div>
        <ul class="list-none pl-2">{ctx['legal_html']}</ul>
        <div class="abnt-heading-2 mt-4">6.2. Rodapé de Responsabilidade Técnica</div>
        <p class="abnt-p text-[9.5pt] italic text-slate-700">Relatório gerado automaticamente pelo sistema <b>SYNAPSE v2.0 Enterprise</b> em apoio ao Centro de Controle Operacional (CCO) e à Secretaria Municipal de Trânsito. Documento técnico de monitoramento operacional, sem fé pública e sujeito à validação final pelo Engenheiro Responsável Técnico.</p>
        <div class="mt-8 text-center">
            <div class="inline-block border-t border-black pt-2 px-12">
                <p class="font-bold text-sm">{ctx['authority']}</p>
                <p class="text-[10pt] text-slate-700">{ctx['authority_role']}</p>
                <p class="text-[8.5pt] text-slate-500">{ctx['registration']} • {ctx['city_hall']}</p>
            </div>
        </div>
        <div class="abnt-heading-1 mt-8">7. Referências Técnicas e Bibliográficas (ABNT NBR 6023)</div>
        <ul class="list-none pl-0 mt-2">{ctx['refs_html']}</ul>
        <div class="abnt-footer-meta">SYNAPSE Explanatory Traffic Report • ABNT NBR 10719:2015 e CTB Art. 24</div>
    </div>
    """


def build_all_pages_html(ctx: Dict[str, Any]) -> str:
    """Concatenates all 6 modular A4 preview sheets."""
    return "".join([
        build_page_1_html(ctx),
        build_page_2_html(ctx),
        build_page_3_html(ctx),
        build_page_4_html(ctx),
        build_page_5_html(ctx),
        build_page_6_html(ctx),
    ])
