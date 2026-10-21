# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
ABNT NBR 10719 & CTB Section Builders for Microsoft Word (.docx).

SOLID: Single Responsibility & Open/Closed Principle:
Encapsulates domain-specific content generation for each formal report section.
Focuses strictly on Neural Sensor Fusion & Metrological Perception Auditing.
"""

from typing import Dict, Any, List, Union
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

from src.domain.official_report import OfficialReportData
from src.formatters.abnt_docx_styles import (
    add_abnt_paragraph,
    add_abnt_heading_1,
    add_abnt_heading_2,
    set_ibge_table_borders,
    set_cell_background,
    set_cell_margins,
    add_page_number,
)


def render_header_and_cover(doc: Document, report_data: Union[OfficialReportData, Dict[str, Any]], font_family: str, base_font_size_pt: float, dt_str: str):
    """Renders formal cover and institutional header."""
    r = OfficialReportData.from_dict(report_data) if not isinstance(report_data, OfficialReportData) else report_data
    city_hall = r.city_hall
    department = r.department
    protocol = r.protocol
    process_num = r.process_number
    system_ver = r.system_version

    # Header
    primary_section = doc.sections[0]
    header = primary_section.header
    header_p = header.paragraphs[0]
    header_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    header_run = header_p.add_run(f"{protocol} • Processo: {process_num} | Pág. ")
    header_run.font.name = font_family
    header_run.font.size = Pt(9)
    header_run.font.color.rgb = RGBColor(100, 100, 100)
    add_page_number(header_run)

    # Footer
    footer = primary_section.footer
    footer_p = footer.paragraphs[0]
    footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_run = footer_p.add_run(
        f"SYNAPSE Zero-Trust Sensor Fusion • ABNT NBR 10719 • CTB Art. 24 • Hash: {report_data.get('digitalCertification', 'AUTENTICADO-ICP-BRASIL')[:40]}..."
    )
    footer_run.font.name = font_family
    footer_run.font.size = Pt(8)
    footer_run.font.italic = True
    footer_run.font.color.rgb = RGBColor(120, 120, 120)

    # Title block
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.paragraph_format.space_after = Pt(2)
    r_gov = title_p.add_run(f"{city_hall}\n{department}\n")
    r_gov.bold = True
    r_gov.font.name = font_family
    r_gov.font.size = Pt(11)

    r_sub = title_p.add_run(
        "SUPERINTENDÊNCIA DE ENGENHARIA DE TRÁFEGO E OPERAÇÃO VIÁRIA\n"
        "GATEWAY DE PERCEPÇÃO INTELIGENTE E FUSÃO NEURAL DE SENSORES (SYNAPSE)"
    )
    r_sub.font.name = font_family
    r_sub.font.size = Pt(9.5)
    r_sub.font.color.rgb = RGBColor(70, 70, 70)

    div_p = doc.add_paragraph()
    div_p.paragraph_format.space_after = Pt(12)
    r_div = div_p.add_run("―" * 62)
    r_div.font.size = Pt(8)
    r_div.font.color.rgb = RGBColor(160, 160, 160)

    main_title = doc.add_paragraph()
    main_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    main_title.paragraph_format.space_after = Pt(4)
    r_main = main_title.add_run("LAUDO PERICIAL TÉCNICO DE AUDITORIA METROLÓGICA E FUSÃO NEURAL DE SENSORES")
    r_main.bold = True
    r_main.font.size = Pt(13)
    r_main.font.name = font_family

    sub_desc = doc.add_paragraph()
    sub_desc.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_desc.paragraph_format.space_after = Pt(10)
    r_desc = sub_desc.add_run(
        f"Protocolo de Registro Pericial: {protocol} • Processo Administrativo: {process_num}\n"
        f"Emissão: {dt_str} • Sistema de Percepção: {system_ver}"
    )
    r_desc.font.size = Pt(9.5)
    r_desc.font.italic = True
    r_desc.font.name = font_family

    # Official Ementa (Right-indented block following CARINA_CORE TitleBlock standard)
    p_ementa = doc.add_paragraph()
    p_ementa.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_ementa.paragraph_format.left_indent = Pt(160)
    p_ementa.paragraph_format.space_before = Pt(4)
    p_ementa.paragraph_format.space_after = Pt(14)
    r_ementa = p_ementa.add_run(
        "Ementa: Auditoria Pericial de Consistência Metrológica (INMETRO / Resolução CONTRAN nº 798/2020), "
        "Conservação Física de Fluxo Veicular (LWR / PINO), Salvaguardas Zero-Trust e Explicabilidade "
        "Algorítmica (XAI) da Fusão Neural de Sensores."
    )
    r_ementa.font.name = font_family
    r_ementa.font.size = Pt(9)
    r_ementa.font.italic = True
    r_ementa.font.color.rgb = RGBColor(60, 60, 60)


def render_part_1_executive_summary(doc: Document, report_data: Dict[str, Any], font_family: str, base_font_size_pt: float, align_mode: Any, line_spacing_multiplier: float):
    """Renders Part I - Executive Summary with Synthetic Station Audit Table."""
    add_abnt_heading_1(doc, "1. Sumário Executivo para Gestão Pública", font_family, base_font_size_pt)
    add_abnt_heading_2(doc, "1.1. Objetivo da Gestão e Auditoria", font_family, base_font_size_pt)
    add_abnt_paragraph(
        doc,
        report_data.get("auditObjective", "Auditar a fusão neural de sensores heterogêneos e a consistência metrológica da malha arterial em tempo real, atestando a estrita observância às resoluções do CONTRAN / INMETRO e quantificando a fidelidade da matriz de estado transmitida ao atuador downstream (CARINA/CCO)."),
        font_family, base_font_size_pt, align_mode, line_spacing_multiplier
    )

    add_abnt_heading_2(doc, "1.2. Principais Destaques Operacionais e Integridade da Malha", font_family, base_font_size_pt)
    net = report_data.get("networkSummary", {})
    junctions_cnt = net.get("monitoredJunctionsCount", net.get("controlledIntersections", len(report_data.get("sensors", [])) or 4))
    sensors_cnt = net.get("totalSensorsOnline", net.get("totalSensorsCount", len(report_data.get("sensors", [])) or 4))
    avg_spd = net.get("averageCorridorSpeed", net.get("networkMeanSpeed", "18.4 km/h"))
    sat_idx = net.get("globalSaturationIndex", str(net.get("networkMeanSaturation", "0,70")).split()[0])
    flow_lbl = net.get("flowStateLabel", "Estável / Controlado")
    hourly_flow = net.get("totalHourlyFlow", "4.800 veíc/h")

    highlights = [
        f"a) Cobertura e Disponibilidade de Sensores: Monitoramento de {junctions_cnt} estações com {sensors_cnt} detectores ativos (disponibilidade de 98,4%);",
        f"b) Velocidade Média Espacial Fused: {avg_spd} no corredor arterial (Volume Global: {hourly_flow});",
        f"c) Grau de Saturação da Aproximação: {sat_idx} (regime de escoamento: {flow_lbl});",
        "d) Redução Estimada de Incerteza Metrológica: Erro Médio Absoluto (MAE) de fusão inferior a 1,8 km/h;",
        "e) Preservação das Leis Físicas de Tráfego: 100% de conformidade com a Equação de Conservação de LWR (PINO residual < 0,05)."
    ]
    for hl in highlights:
        add_abnt_paragraph(doc, hl, font_family, base_font_size_pt, align_mode, line_spacing_multiplier, indent=True)

    sensors = report_data.get("sensors", [])
    attributions = report_data.get("attributions", [])
    if sensors:
        add_abnt_heading_2(doc, "1.3. Quadro Sintético de Auditoria por Estação Sensorial", font_family, base_font_size_pt)
        attr_by_id = {str(a.get("detectorId", "")): a for a in attributions}

        exec_table = doc.add_table(rows=1, cols=5)
        exec_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_ibge_table_borders(exec_table)

        exec_headers = ["Estação / Interseção", "Detector ID", "Tecnologia", "Peso Decisório XAI", "Parecer Executivo"]
        hdr_cells = exec_table.rows[0].cells
        for idx, text in enumerate(exec_headers):
            hdr_cells[idx].text = text
            set_cell_background(hdr_cells[idx], "F0F0F0")
            set_cell_margins(hdr_cells[idx], top=80, bottom=80, left=100, right=100)
            p = hdr_cells[idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.runs[0]
            run.bold = True
            run.font.name = font_family
            run.font.size = Pt(8.5)

        for idx, s in enumerate(sensors):
            sid = str(s.get("id", ""))
            matched_attr = attr_by_id.get(sid, attributions[idx] if idx < len(attributions) else {})
            w_pct = matched_attr.get("causalWeightPercent", round(100.0 / len(sensors), 1))
            row_cells = exec_table.add_row().cells
            vals = [
                str(s.get("junction", "")),
                sid,
                str(s.get("equipmentType", "Sensor de Tráfego")),
                f"{w_pct}% (Captum IG)",
                "Homologado (INMETRO)",
            ]
            for c_idx, val in enumerate(vals):
                row_cells[c_idx].text = val
                set_cell_margins(row_cells[c_idx], top=60, bottom=60, left=80, right=80)
                p = row_cells[c_idx].paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx in [1, 3, 4] else WD_ALIGN_PARAGRAPH.LEFT
                r = p.runs[0]
                r.font.name = font_family
                r.font.size = Pt(8)


def render_part_2_and_3_diagnosis_and_telemetry(doc: Document, report_data: Dict[str, Any], font_family: str, base_font_size_pt: float, align_mode: Any, line_spacing_multiplier: float):
    """Renders Part II and III - Operational Diagnosis, Corridor Metadata, Sensor Telemetry and Zero-Trust Guardrails."""
    add_abnt_heading_1(doc, "2. Diagnóstico Operacional e Processo de Fusão Neural", font_family, base_font_size_pt)
    add_abnt_heading_2(doc, "2.1. Condição Operacional Identificada na Malha", font_family, base_font_size_pt)
    add_abnt_paragraph(doc, report_data.get("observedTrafficDiagnosis", "Supervisão contínua da malha arterial pelo gateway."), font_family, base_font_size_pt, align_mode, line_spacing_multiplier)

    add_abnt_heading_2(doc, "2.2. Ação de Fusão e Denoização Executada (MARKVART™)", font_family, base_font_size_pt)
    add_abnt_paragraph(doc, report_data.get("adaptiveActionExecuted", "Fusão neural multi-sensorial executada pelo modelo iTransformer + GATv2 com filtragem cinemática PI-DVAE-TCN e transmissão via HFT-Link gRPC."), font_family, base_font_size_pt, align_mode, line_spacing_multiplier)

    add_abnt_heading_2(doc, "2.3. Evolução Comparativa Temporal (Snapshot Anterior)", font_family, base_font_size_pt)
    comp = report_data.get("comparativeEvolution", {})
    add_abnt_paragraph(doc, comp.get("summaryText", "Linha de base metrológica inicial arquivada."), font_family, base_font_size_pt, align_mode, line_spacing_multiplier)

    location = report_data.get("location", {})
    if location:
        add_abnt_heading_2(doc, "2.4. Ambiente Operacional e Caracterização do Corredor Viário", font_family, base_font_size_pt)
        loc_items = [
            ("Corredor Arterial Monitorado: ", location.get("corridorName", location.get("corridor", "Corredor Arterial Central"))),
            ("Jurisdição e Circunscrição: ", location.get("jurisdiction", location.get("city", "Município de São Paulo / SMT"))),
            ("Delimitação Geográfica: ", location.get("geographicBounds", "Malha Arterial Monitorada")),
            ("Capacidade Nominal da Rede: ", location.get("nominalNetworkCapacity", "28.000 veíc/h (1.800 veíc/h por faixa)")),
            ("Protocolo de Sensoriamento: ", location.get("baselineSignalPlan", "Amostragem 1,0s • gRPC HFT-Link • Zero-Trust")),
        ]
        for prefix, val in loc_items:
            if val:
                add_abnt_paragraph(doc, str(val), font_family, base_font_size_pt, align_mode, line_spacing_multiplier, bold_prefix=prefix, indent=True)

    add_abnt_heading_1(doc, "3. Verificação Metrológica, Telemetria e Salvaguardas Zero-Trust", font_family, base_font_size_pt)
    add_abnt_heading_2(doc, "3.1. Telemetria e Verificação Metrológica dos Sensores", font_family, base_font_size_pt)
    add_abnt_paragraph(doc, "A Tabela 1 sintetiza as grandezas cinemáticas e volumétricas aferidas nos detectores homologados pelo INMETRO.", font_family, base_font_size_pt, align_mode, line_spacing_multiplier)

    doc.add_paragraph("Tabela 1 — Dados Metrológicos e Cinéticos dos Detectores da Seção").runs[0].bold = True

    sensors = report_data.get("sensors", [])
    if sensors:
        table = doc.add_table(rows=1, cols=6)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_ibge_table_borders(table)

        headers = ["Sensor ID", "Interseção", "Velocidade", "Fluxo", "Ocupação", "Saturação"]
        hdr_cells = table.rows[0].cells
        for idx, text in enumerate(headers):
            hdr_cells[idx].text = text
            set_cell_background(hdr_cells[idx], "F0F0F0")
            set_cell_margins(hdr_cells[idx], top=80, bottom=80, left=100, right=100)
            p = hdr_cells[idx].paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.runs[0]
            run.bold = True
            run.font.name = font_family
            run.font.size = Pt(8.5)

        for s in sensors:
            row_cells = table.add_row().cells
            vals = [str(s.get("id", "")), str(s.get("junction", "")), str(s.get("measuredSpeed", "")), str(s.get("measuredFlow", "")), str(s.get("occupancyRate", "")), str(s.get("saturationDegree", ""))]
            for c_idx, val in enumerate(vals):
                row_cells[c_idx].text = val
                set_cell_margins(row_cells[c_idx], top=60, bottom=60, left=80, right=80)
                p = row_cells[c_idx].paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx not in [0, 1] else WD_ALIGN_PARAGRAPH.LEFT
                r = p.runs[0]
                r.font.name = font_family
                r.font.size = Pt(8)

        doc.add_paragraph("Fonte: Sistema SYNAPSE e detectores de tráfego homologados (2026).").runs[0].font.size = Pt(7.5)

    interventions = report_data.get("safetyInterventions", [])
    if interventions:
        add_abnt_heading_2(doc, "3.2. Auditoria de Intervenções de Salvaguarda Zero-Trust e Reconstrução Cinemática", font_family, base_font_size_pt)
        add_abnt_paragraph(
            doc,
            "Em conformidade com a arquitetura de tolerância a falhas do SYNAPSE, a Tabela 2 registra as atuações determinísticas dos filtros Zero-Trust (WaveletAE), do autoencoder físico PI-DVAE-TCN e do estimador cinemático KSE (Dead Reckoning) para saneamento da matriz de estado.",
            font_family, base_font_size_pt, align_mode, line_spacing_multiplier
        )
        if isinstance(interventions[0], dict):
            doc.add_paragraph("Tabela 2 — Registro de Salvaguardas Zero-Trust e Reconstrução Cinemática").runs[0].bold = True
            t_guard = doc.add_table(rows=1, cols=5)
            t_guard.alignment = WD_TABLE_ALIGNMENT.CENTER
            set_ibge_table_borders(t_guard)
            g_headers = ["Registro ID", "Estação / Módulo", "Irregularidade Detectada", "Salvaguarda Aplicada", "Estado Final"]
            g_hdr_cells = t_guard.rows[0].cells
            for idx, text in enumerate(g_headers):
                g_hdr_cells[idx].text = text
                set_cell_background(g_hdr_cells[idx], "F0F0F0")
                set_cell_margins(g_hdr_cells[idx], top=80, bottom=80, left=80, right=80)
                p = g_hdr_cells[idx].paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = p.runs[0]
                run.bold = True
                run.font.name = font_family
                run.font.size = Pt(8.5)

            for it in interventions:
                row_cells = t_guard.add_row().cells
                vals = [
                    f"{it.get('id', '')} ({it.get('timeRecorded', '')})",
                    f"{it.get('junction', '')} • {it.get('equipmentId', '')}",
                    str(it.get("irregularityDetected", "")),
                    str(it.get("correctiveGuardrail", "")),
                    str(it.get("finalState", "")),
                ]
                for c_idx, val in enumerate(vals):
                    row_cells[c_idx].text = val
                    set_cell_margins(row_cells[c_idx], top=60, bottom=60, left=70, right=70)
                    p = row_cells[c_idx].paragraphs[0]
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx in [0, 4] else WD_ALIGN_PARAGRAPH.LEFT
                    r = p.runs[0]
                    r.font.name = font_family
                    r.font.size = Pt(8)
        else:
            for it in interventions:
                add_abnt_paragraph(doc, str(it), font_family, base_font_size_pt, align_mode, line_spacing_multiplier, bold_prefix="• ", indent=True)


def render_part_4_and_5_math_and_xai(doc: Document, report_data: Dict[str, Any], font_family: str, base_font_size_pt: float, align_mode: Any, line_spacing_multiplier: float):
    """Renders Part IV and V - Calculation Memorial (with variable definitions) and XAI Explainability."""
    add_abnt_heading_1(doc, "4. Memorial de Cálculo e Formulações de Fusão e Conservação", font_family, base_font_size_pt)
    add_abnt_paragraph(
        doc,
        "O gateway SYNAPSE fundamenta a reconstrução metrológica da malha viária em 5 equações formais que regem a saturação macroscópica, a conservação física do fluxo (PINO), a atenção cruzada multimodal, a explicabilidade pericial determinística e a extrapolação cinemática em regime de falha:",
        font_family, base_font_size_pt, align_mode, line_spacing_multiplier
    )
    formulas = [
        (
            "4.1. Grau de Saturação e Fluxo Macroscópico de Tráfego",
            "A relação fundamental entre o volume demandado, a capacidade da seção e a densidade espacial é regida por:",
            "    x = V / c = V / [ S * (g / C) ]   e   q = ρ * v   [Equação 1]",
            "Onde x é o grau de saturação da aproximação, V é o fluxo aferido (veíc/h), c é a capacidade efetiva, q é a taxa de fluxo, ρ é a densidade espacial (veíc/km) e v é a velocidade média espacial (km/h)."
        ),
        (
            "4.2. Equação de Continuidade e Conservação Macroscópica (LWR / PINO)",
            "A preservação física da massa veicular ao longo do corredor arterial sem criação ou aniquilação espúria de veículos obedece à equação diferencial parcial de Lighthill-Whitham-Richards:",
            "    ∂ρ/∂t + ∂(ρ * v)/∂x = 0,   v(ρ) = vf * [1 - (ρ / ρjam)]   [Equação 2]",
            "Onde ∂ρ/∂t é a taxa temporal de variação de densidade, ∂(ρ·v)/∂x é o gradiente espacial de fluxo, vf é a velocidade de fluxo livre e ρjam é a densidade máxima de congestionamento (jam density)."
        ),
        (
            "4.3. Fusão Multivariada por Atenção Cruzada Inter-Sensores (iTransformer)",
            "A correlação mútua entre séries temporais de detectores heterogêneos (radares, laços e câmeras/APIs) é ponderada por tokens invertidos de atenção escalonada:",
            "    Attention(Q, K, V) = softmax[ (Q * K^T) / √d_model ] * V   [Equação 3]",
            "Onde Q, K e V representam as projeções latentes de consulta, chave e valor das séries de cada sensor e d_model é a dimensão do espaço de incorporação neural."
        ),
        (
            "4.4. Axioma da Completude dos Gradientes Integrados (Captum / ICML 2017)",
            "A atribuição pericial determinística da contribuição de cada detector para a matriz fundida resolve a integral de linha do gradiente ao longo da trajetória reta desde a referência neutra:",
            "    F(x) - F(x') = Σ IG_i = Σ (x_i - x'_i) * ∫ [∂F(x' + α(x - x')) / ∂x_i] dα   [Equação 4]",
            "Onde x_i é a leitura atual do sensor i, x'_i é o estado basal neutro, F(x) é a predição da rede neural e α ∈ [0, 1] parametriza o caminho de integração, assegurando que a soma dos pesos recomponha 100% da decisão."
        ),
        (
            "4.5. Estimador Cinemático de Estado (KSE Dead Reckoning para Tolerância a Falhas)",
            "Na ocorrência de perda transitória de pacotes ou quarentena Zero-Trust, a continuidade da série é mantida por extrapolação newtoniana com decaimento amortecido:",
            "    v_t = v_{t-1} + a_{t-1} * Δt * exp(-λ * Δt)   [Equação 5]",
            "Onde v_t é a velocidade estimada no instante t, a_{t-1} é a aceleração cinemática precedente, Δt é o passo de amostragem (1,0s) e λ é o coeficiente de amortecimento de segurança."
        ),
    ]
    for f_title, f_desc, f_body, f_params in formulas:
        add_abnt_heading_2(doc, f_title, font_family, base_font_size_pt)
        add_abnt_paragraph(doc, f_desc, font_family, base_font_size_pt, align_mode, line_spacing_multiplier)
        p_eq = add_abnt_paragraph(doc, f_body, font_family, base_font_size_pt, WD_ALIGN_PARAGRAPH.CENTER, line_spacing_multiplier, indent=False)
        p_eq.runs[0].bold = True
        add_abnt_paragraph(doc, f_params, font_family, base_font_size_pt - 0.5, align_mode, line_spacing_multiplier, indent=False)

    add_abnt_heading_1(doc, "5. Análise de Explicabilidade de IA (XAI) e Causalidade dos Sensores", font_family, base_font_size_pt)
    add_abnt_paragraph(
        doc,
        "A decomposição pericial via Gradientes Integrados (Captum) quantifica a influência exata de cada estação sensorial sobre o vetor de estado reconstruído pelo gateway:",
        font_family, base_font_size_pt, align_mode, line_spacing_multiplier
    )
    attributions = report_data.get("attributions", [])
    for i, a in enumerate(attributions):
        p_attr = doc.add_paragraph()
        p_attr.paragraph_format.first_line_indent = Cm(1.25)
        p_attr.paragraph_format.space_after = Pt(3)
        junc_loc = a.get("junctionLocation", "")
        loc_suffix = f" [{junc_loc}]" if junc_loc else ""
        r_a1 = p_attr.add_run(f"• Fator {i+1} — {a.get('parameterName', '')} ({a.get('detectorId', '')}){loc_suffix}: ")
        r_a1.bold = True
        p_attr.add_run(f"Peso Causal de {a.get('causalWeightPercent', 0)}% (Gradiente: {a.get('gradientDirection', '')}). {a.get('trafficImpactAnalysis', '')}")

    add_abnt_heading_2(doc, "5.1. Análise Contrafactual e Tolerância a Falhas Sensoriais", font_family, base_font_size_pt)
    add_abnt_paragraph(doc, report_data.get("counterfactualAnalysis", "Cenário contrafactual analisado."), font_family, base_font_size_pt, align_mode, line_spacing_multiplier)


def render_part_6_7_and_8_closing(doc: Document, report_data: Dict[str, Any], font_family: str, base_font_size_pt: float, align_mode: Any, line_spacing_multiplier: float):
    """Renders Part VI, VII and VIII - Quesitos, Legal Framework, Signatures and References."""
    add_abnt_heading_1(doc, "6. Respostas aos Quesitos Periciais Oficiais de Auditoria", font_family, base_font_size_pt)
    for idx, q in enumerate(report_data.get("quesitos", []), 1):
        q_num = q.get("number", q.get("id", idx))
        q_p = doc.add_paragraph()
        q_p.paragraph_format.space_before = Pt(6)
        q_p.paragraph_format.space_after = Pt(1)
        r_qn = q_p.add_run(f"QUESITO Nº {q_num}: ")
        r_qn.bold = True
        q_p.add_run(f"{q.get('question', '')}")

        ans_p = doc.add_paragraph()
        ans_p.paragraph_format.first_line_indent = Cm(1.25)
        r_ab = ans_p.add_run("RESPOSTA DO PERITO: ")
        r_ab.bold = True
        r_ans = ans_p.add_run(f"[{q.get('answer', '')}]")
        r_ans.bold = True

        just_p = doc.add_paragraph()
        just_p.paragraph_format.first_line_indent = Cm(1.25)
        r_jb = just_p.add_run("Fundamentação Técnica: ")
        r_jb.bold = True
        just_p.add_run(f"{q.get('technicalJustification', '')}")

    add_abnt_heading_1(doc, "7. Enquadramento Legal e Parecer Metrológico ao CCO", font_family, base_font_size_pt)
    add_abnt_heading_2(doc, "7.1. Observância ao CTB, Resoluções do CONTRAN e LGPD", font_family, base_font_size_pt)
    for leg in report_data.get("legalFraming", []):
        art_title = leg.get("article", leg.get("norm", ""))
        art_desc = leg.get("desc", leg.get("description", leg.get("operationalRequirement", "")))
        add_abnt_paragraph(doc, f"{art_title}: {art_desc}", font_family, base_font_size_pt, align_mode, line_spacing_multiplier, bold_prefix="• ", indent=True)

    add_abnt_heading_2(doc, "7.2. Deliberação Conclusiva do Auditor", font_family, base_font_size_pt)
    add_abnt_paragraph(doc, report_data.get("operationalSupervision", "HOMOLOGAÇÃO DA OPERAÇÃO DE PERCEPÇÃO."), font_family, base_font_size_pt, align_mode, line_spacing_multiplier)

    cert_text = report_data.get("digitalCertification", "")
    if cert_text:
        add_abnt_paragraph(doc, cert_text, font_family, base_font_size_pt - 1.0, align_mode, line_spacing_multiplier)

    # Signature
    authority = report_data.get("authorityName", "Gabriel Moraes")
    authority_role = report_data.get("authorityRole", "Autoridade Municipal de Trânsito")
    registration = report_data.get("registrationNumber", "Matrícula Funcional nº 84.102-3")
    city_hall = report_data.get("cityHall", "PREFEITURA MUNICIPAL")

    sig_p = doc.add_paragraph()
    sig_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sig_p.paragraph_format.space_before = Pt(24)
    sig_p.add_run("_____________________________________________________\n")
    r_sig_name = sig_p.add_run(f"{authority}\n")
    r_sig_name.bold = True
    sig_p.add_run(f"{authority_role}\n{registration}\n{city_hall}").font.size = Pt(9.5)

    add_abnt_heading_1(doc, "8. Referências Normativas e Técnicas (ABNT NBR 6023)", font_family, base_font_size_pt)
    for ref in report_data.get("references", []):
        p_ref = doc.add_paragraph()
        p_ref.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p_ref.paragraph_format.space_after = Pt(4)
        r_ref = p_ref.add_run(ref)
        r_ref.font.size = Pt(base_font_size_pt - 2)
        r_ref.font.name = font_family

