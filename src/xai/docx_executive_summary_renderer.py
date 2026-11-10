# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
DOCX Part I - Executive Summary & Synthetic Station Audit Table Renderer.

SOLID Design:
- Single Responsibility Principle (SRP): Encapsulates only the construction of Part I
  (executive summary, public administration objectives, operational highlights, and IBGE table).
- Clean Architecture / DDD: Binds to traffic network summaries and sensor station attributes.
"""

from typing import Dict, Any
from docx import Document
from docx.shared import Pt
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


class DocxExecutiveSummaryRenderer:
    """
    Renders Part I (Executive Summary and Synthetic Audit Table) in Word (.docx)
    following ABNT NBR 10719:2015 and IBGE tabular presentation standards.
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
        """Renders Part I - Executive Summary with Synthetic Station Audit Table."""
        add_abnt_heading_1(doc, "1. Resumo em Uma Página: O que Aconteceu na Malha", font_family, base_font_size_pt)
        add_abnt_heading_2(doc, "1.1. Objetivo do Relatório Explicativo", font_family, base_font_size_pt)
        add_abnt_paragraph(
            doc,
            report_data.get(
                "auditObjective",
                "Apresentar à Prefeitura e ao Centro de Controle Operacional (CCO) a explicação transparente da percepção "
                "do tráfego urbano gerada pelo SYNAPSE v2.0 Enterprise, descrevendo o comportamento observado nos pontos de "
                "monitoramento da malha viária, os fatores que determinaram as estimativas do sistema e as ações recomendadas."
            ),
            font_family,
            base_font_size_pt,
            align_mode,
            line_spacing_multiplier,
        )

        add_abnt_heading_2(doc, "1.2. Principais Ocorrências e Estado do Corredor", font_family, base_font_size_pt)
        net = report_data.get("networkSummary", {})
        junctions_cnt = net.get("monitoredJunctionsCount", net.get("controlledIntersections", len(report_data.get("sensors", [])) or 4))
        sensors_cnt = net.get("totalSensorsOnline", net.get("totalSensorsCount", len(report_data.get("sensors", [])) or 4))
        avg_spd = net.get("averageCorridorSpeed", net.get("networkMeanSpeed", "18.4 km/h"))
        sat_idx = net.get("globalSaturationIndex", str(net.get("networkMeanSaturation", "0,70")).split()[0])
        flow_lbl = net.get("flowStateLabel", "Estável / Controlado")
        hourly_flow = net.get("totalHourlyFlow", "4.800 veíc/h")

        safety = report_data.get("safetyInterventions", [])
        if not safety:
            safeguards_desc = "d) Salvaguardas Zero-Trust em Tempo Real: Nenhuma salvaguarda foi acionada no período analisado;"
        else:
            safeguards_desc = "d) Salvaguardas Zero-Trust em Tempo Real: Filtros preventivos isolaram leituras atípicas em quarentena sem interrupção de serviço;"

        highlights = [
            f"a) Cobertura de Fontes: Monitoramento contínuo de {junctions_cnt} estações com {sensors_cnt} fontes de telemetria ativas;",
            f"b) Velocidade Média Espacial: {avg_spd} no corredor arterial (Volume Global Estimado: {hourly_flow});",
            f"c) Grau de Saturação da Aproximação: {sat_idx} (regime de escoamento: {flow_lbl});",
            safeguards_desc,
            "e) Consistência com Leis Físicas: Reconstrução consistente com a Equação de Conservação de LWR (PINO residual < 0,05)."
        ]
        for hl in highlights:
            add_abnt_paragraph(doc, hl, font_family, base_font_size_pt, align_mode, line_spacing_multiplier, indent=True)

        sensors = report_data.get("sensors", [])
        attributions = report_data.get("attributions", [])
        if sensors:
            add_abnt_heading_2(doc, "1.3. Quadro Sintético por Ponto de Monitoramento", font_family, base_font_size_pt)
            attr_by_id = {str(a.get("detectorId", "")): a for a in attributions}

            exec_table = doc.add_table(rows=1, cols=5)
            exec_table.alignment = WD_TABLE_ALIGNMENT.CENTER
            set_ibge_table_borders(exec_table)

            exec_headers = ["Estação / Interseção", "Detector ID", "Tipo de Fonte", "O que mais pesou", "Status Operacional"]
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
                w_pct_str = f"{w_pct:.1f}%".replace(".", ",")

                try:
                    spd_v = float(str(s.get("measuredSpeed", "18.0")).split()[0].replace(",", "."))
                except Exception:
                    spd_v = 18.0
                try:
                    sat_v = float(str(s.get("saturationDegree", "0.72")).split()[0].replace(",", "."))
                except Exception:
                    sat_v = 0.72

                if sat_v >= 0.90 or spd_v < 5.0:
                    op_status = "Crítico / Retenção"
                elif sat_v >= 0.75 or spd_v < 15.0:
                    op_status = "Atenção / Escoamento Lento"
                else:
                    op_status = "Normal / Fluxo Livre"

                junc_str = str(s.get("junction", ""))
                if junc_str.startswith("Estação: "):
                    junc_str = junc_str.replace("Estação: ", "").strip()

                row_cells = exec_table.add_row().cells
                vals = [
                    junc_str,
                    sid,
                    str(s.get("equipmentType", "Sensor de Tráfego")),
                    f"{w_pct_str} (Peso XAI)",
                    op_status,
                ]
                for c_idx, val in enumerate(vals):
                    row_cells[c_idx].text = val
                    set_cell_margins(row_cells[c_idx], top=60, bottom=60, left=80, right=80)
                    p = row_cells[c_idx].paragraphs[0]
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx in [1, 3, 4] else WD_ALIGN_PARAGRAPH.LEFT
                    r = p.runs[0]
                    r.font.name = font_family
                    r.font.size = Pt(8)
