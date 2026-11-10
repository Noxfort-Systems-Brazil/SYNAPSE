# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
DOCX Part IV & V - Calculation Memorial & XAI Causal Attribution Renderer.

SOLID Design:
- Single Responsibility Principle (SRP): Encapsulates only the formal presentation of mathematical
  equations (HCM saturation, LWR/PINO continuity, iTransformer attention, Captum integrated gradients,
  and KSE dead reckoning) along with sensor causal attributions and counterfactual analysis.
- Clean Architecture / DDD: Binds to XAI attribution entities and parameter definitions.
"""

from typing import Dict, Any
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

from src.formatters.abnt_docx_styles import (
    add_abnt_paragraph,
    add_abnt_heading_1,
    add_abnt_heading_2,
    set_ibge_table_borders,
    set_cell_background,
    set_cell_margins,
)


class DocxMathXaiRenderer:
    """
    Renders Section 3 (Why the system reached this conclusion - XAI causal weights),
    Section 4 (What the system corrected or quarantined - Safeguards Table),
    and Technical Annex (5 formal perception and conservation equations) into Word (.docx).
    """

    def render(
        self,
        doc: Document,
        report_data: Dict[str, Any],
        font_family: str,
        base_font_size_pt: float,
        align_mode: Any,
        line_spacing_multiplier: float,
    ) -> None:
        """Renders Section 3 (XAI Attributions) and Section 4 (Safeguards Table)."""
        # --- SEÇÃO 3: POR QUE CHEGOU A ESSA CONCLUSÃO: FATORES DE MAIOR PESO (XAI) ---
        add_abnt_heading_1(doc, "3. Por que Chegou a Essa Conclusão: Fatores de Maior Peso (XAI)", font_family, base_font_size_pt)
        add_abnt_paragraph(
            doc,
            "A explicabilidade algorítmica do SYNAPSE revela como o modelo distribuiu o peso entre as variáveis cinemáticas observadas. "
            "As atribuições a seguir quantificam a contribuição relativa de cada fator calculada pelo método de Gradientes Integrados:",
            font_family,
            base_font_size_pt,
            align_mode,
            line_spacing_multiplier,
            indent=True,
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
            w_raw = a.get('causalWeightPercent', 0)
            w_str = f"{float(w_raw):.1f}%".replace(".", ",") if isinstance(w_raw, (int, float)) or str(w_raw).replace('.', '', 1).isdigit() else f"{w_raw}%"
            p_attr.add_run(f"Peso de Relevância de {w_str} (Gradiente: {a.get('gradientDirection', '')}). {a.get('trafficImpactAnalysis', '')}")

        add_abnt_heading_2(doc, "3.1. Análise Contrafactual e Tolerância a Falhas Sensoriais", font_family, base_font_size_pt)
        add_abnt_paragraph(doc, report_data.get("counterfactualAnalysis", "Cenário contrafactual analisado."), font_family, base_font_size_pt, align_mode, line_spacing_multiplier, indent=True)

        # --- SEÇÃO 4: O QUE O SISTEMA CORRIGIU OU ISOLOU (SALVAGUARDAS OPERACIONAIS) ---
        add_abnt_heading_1(doc, "4. O que o Sistema Corrigiu ou Isolou (Salvaguardas Operacionais)", font_family, base_font_size_pt)
        add_abnt_paragraph(
            doc,
            "Para evitar contaminação do plano semafórico por ruídos ou falhas pontuais de transmissão, o SYNAPSE opera com "
            "salvaguardas preventivas. A Tabela 2 documenta as intervenções automáticas registradas:",
            font_family,
            base_font_size_pt,
            align_mode,
            line_spacing_multiplier,
            indent=True,
        )

        interventions = report_data.get("safetyInterventions", [])
        if interventions:
            if isinstance(interventions[0], dict):
                doc.add_paragraph("Tabela 2 — Registro de Salvaguardas e Contenção de Anomalias").runs[0].bold = True
                t_guard = doc.add_table(rows=1, cols=5)
                t_guard.alignment = WD_TABLE_ALIGNMENT.CENTER
                set_ibge_table_borders(t_guard)
                g_headers = ["Registro ID", "Estação / Sensor", "Evento Detectado", "Salvaguarda Aplicada", "Estado Final"]
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
                    eq_id = str(it.get('equipmentId', ''))
                    if "PI_DVAE" in eq_id:
                        eq_id = "CAM_OCR_01"
                    elif "KSE" in eq_id:
                        eq_id = "DET_REBOUCAS_01"
                    vals = [
                        f"{it.get('id', '')} ({it.get('timeRecorded', '')})",
                        f"{it.get('junction', '')} • {eq_id}",
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
                    add_abnt_paragraph(
                        doc,
                        str(it),
                        font_family,
                        base_font_size_pt,
                        align_mode,
                        line_spacing_multiplier,
                        bold_prefix="• ",
                        indent=True,
                    )

    def render_technical_annex_equations(
        self,
        doc: Document,
        font_family: str,
        base_font_size_pt: float,
        align_mode: Any,
        line_spacing_multiplier: float,
    ) -> None:
        """Renders Technical Annex: Perception and Conservation Equations (Equations 1-5)."""
        add_abnt_heading_1(doc, "ANEXO TÉCNICO: Memorial de Cálculo e Formulações de Percepção", font_family, base_font_size_pt)
        add_abnt_paragraph(
            doc,
            "Para análise aprofundada de engenharia, a modelagem de tráfego, a conservação física do fluxo veicular e a explicabilidade "
            "do motor SYNAPSE fundamentam-se nas 5 equações a seguir:",
            font_family,
            base_font_size_pt,
            align_mode,
            line_spacing_multiplier,
            indent=True,
        )

        formulas = [
            (
                "A.1. Grau de Saturação e Fluxo Macroscópico de Tráfego",
                "A relação fundamental entre o volume demandado, a capacidade da seção e a densidade espacial é regida por:",
                "    x = V / c = V / [ S * (g / C) ]   e   q = ρ * v   [Equação A.1]",
                "Onde x é o grau de saturação da aproximação, V é o fluxo aferido (veíc/h), c é a capacidade efetiva, "
                "q é a taxa de fluxo, ρ é a densidade espacial (veíc/km) e v é a velocidade média espacial (km/h)."
            ),
            (
                "A.2. Equação de Continuidade e Conservação Macroscópica (LWR / PINO)",
                "A preservação física da massa veicular ao longo do corredor arterial sem criação ou aniquilação espúria de "
                "veículos obedece à equação diferencial parcial de Lighthill-Whitham-Richards:",
                "    ∂ρ/∂t + ∂(ρ * v)/∂x = 0,   v(ρ) = vf * [1 - (ρ / ρjam)]   [Equação A.2]",
                "Onde ∂ρ/∂t é a taxa temporal de variação de densidade, ∂(ρ·v)/∂x é o gradiente espacial de fluxo, "
                "vf é a velocidade de fluxo livre e ρjam é a densidade máxima de congestionamento (jam density)."
            ),
            (
                "A.3. Fusão Multivariada por Atenção Cruzada Inter-Sensores (iTransformer)",
                "A correlação mútua entre séries temporais de detectores heterogêneos (radares, laços e câmeras/APIs) é ponderada "
                "por tokens invertidos de atenção escalonada:",
                "    Attention(Q, K, V) = softmax[ (Q * K^T) / √d_model ] * V   [Equação A.3]",
                "Onde Q, K e V representam as projeções latentes de consulta, chave e valor das séries de cada sensor e "
                "d_model é a dimensão do espaço de incorporação neural."
            ),
            (
                "A.4. Axioma da Completude dos Gradientes Integrados (Método Captum)",
                "A decomposição matemática da contribuição de cada variável sensorial para a estimativa do estado de tráfego "
                "resolve a integral de linha do gradiente ao longo da trajetória reta desde a referência neutra:",
                "    F(x) - F(x') = Σ IG_i = Σ (x_i - x'_i) * ∫ [∂F(x' + α(x - x')) / ∂x_i] dα   [Equação A.4]",
                "Onde x_i é a leitura atual do sensor i, x'_i é o estado basal neutro (fluxo livre), F(x) é a estimativa do modelo neural SYNAPSE e "
                "α ∈ [0, 1] parametriza o caminho de integração, distribuindo a variação da estimativa entre as variáveis de entrada sem parcelas inexplicadas."
            ),
            (
                "A.5. Estimador Cinemático de Estado (Dead Reckoning com Amortecimento)",
                "Na ocorrência de perda transitória de pacotes ou isolamento preventivo, a continuidade da série é mantida "
                "por extrapolação cinemática com decaimento amortecido:",
                "    v_t = v_{t-1} + a_{t-1} * Δt * exp(-λ * Δt)   [Equação A.5]",
                "Onde v_t é a velocidade estimada no instante t, a_{t-1} é a aceleração cinemática precedente, "
                "Δt é o passo de amostragem (1,0s) e λ é o coeficiente de amortecimento de segurança."
            ),
        ]

        for f_title, f_desc, f_body, f_params in formulas:
            add_abnt_heading_2(doc, f_title, font_family, base_font_size_pt)
            add_abnt_paragraph(doc, f_desc, font_family, base_font_size_pt, align_mode, line_spacing_multiplier)
            p_eq = add_abnt_paragraph(doc, f_body, font_family, base_font_size_pt, WD_ALIGN_PARAGRAPH.CENTER, line_spacing_multiplier, indent=False)
            p_eq.runs[0].bold = True
            add_abnt_paragraph(doc, f_params, font_family, base_font_size_pt - 0.5, align_mode, line_spacing_multiplier, indent=False)
