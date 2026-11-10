# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
DOCX Part II & III - Operational Diagnosis, Sensor Telemetry and Zero-Trust Guardrails Renderer.

SOLID Design:
- Single Responsibility Principle (SRP): Encapsulates operational diagnosis, MARKVART™ action,
  corridor metadata, Table 1 (Sensor Metrology & Telemetry), and Table 2 (Zero-Trust Interventions).
- Clean Architecture / DDD: Connects directly with sensor domain entities and guardrail logs.
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


class DocxTelemetryGuardianRenderer:
    """
    Renders Part II (Operational Diagnosis) and Part III (Metrological Telemetry
    and Zero-Trust Safety Interventions) into Microsoft Word (.docx).
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
        """Renders Section 2 - O que o Sistema Viu: Fontes, Telemetria e Qualidade."""
        # --- SEÇÃO 2: O QUE O SISTEMA VIU: TELEMETRIA E FONTES DE DADOS ---
        add_abnt_heading_1(doc, "2. O que o Sistema Viu: Fontes, Amostragem e Qualidade", font_family, base_font_size_pt)

        # 2.1 Contexto Operacional e Caracterização do Corredor
        add_abnt_heading_2(doc, "2.1. Contexto Operacional e Caracterização das Fontes", font_family, base_font_size_pt)
        add_abnt_paragraph(
            doc,
            report_data.get("observedTrafficDiagnosis", "Supervisão contínua da malha arterial pelo gateway."),
            font_family,
            base_font_size_pt,
            align_mode,
            line_spacing_multiplier,
            indent=True,
        )

        location = report_data.get("location", {})
        if location:
            loc_items = [
                ("Corredor Arterial Monitorado: ", location.get("corridorName", location.get("corridor", "Corredor Arterial Central"))),
                ("Jurisdição e Circunscrição: ", location.get("jurisdiction", location.get("city", "Município de São Paulo / SMT"))),
                ("Delimitação Geográfica: ", location.get("geographicBounds", "Malha Arterial Monitorada")),
                ("Capacidade Nominal da Rede: ", location.get("nominalNetworkCapacity", "28.000 veíc/h (1.800 veíc/h por faixa)")),
                ("Protocolo de Sensoriamento: ", location.get("baselineSignalPlan", "Amostragem 1,0s • gRPC HFT-Link • Zero-Trust")),
            ]
            for prefix, val in loc_items:
                if val:
                    add_abnt_paragraph(
                        doc,
                        str(val),
                        font_family,
                        base_font_size_pt,
                        align_mode,
                        line_spacing_multiplier,
                        bold_prefix=prefix,
                        indent=True,
                    )

        add_abnt_paragraph(
            doc,
            "O gateway SYNAPSE integra fontes heterogêneas com naturezas metrológicas distintas:\n"
            "• Detectores Físicos (Radares Doppler e Laços Indutivos): Medição cinemática direta de velocidade e contagem veicular pontual na via.\n"
            "• Visão Computacional (Câmeras OCR): Processamento de imagem para cálculo de densidade espacial e taxa de ocupação visual.\n"
            "• Feeds Agregados de Mobilidade (APIs de Terceiros - ex: Waze, TomTom): Dados médios por amostragem de usuários para contexto macroscópico, sem aferição direta de instrumentos de campo.",
            font_family,
            base_font_size_pt - 0.5,
            align_mode,
            line_spacing_multiplier,
            indent=True,
        )

        # 2.2 Telemetria Cinética das Fontes de Dados
        add_abnt_heading_2(doc, "2.2. Telemetria Cinética das Fontes de Dados", font_family, base_font_size_pt)
        add_abnt_paragraph(
            doc,
            "A Tabela 1 sintetiza as grandezas cinemáticas e operacionais aferidas pelas fontes de telemetria ativas na malha arterial:",
            font_family,
            base_font_size_pt,
            align_mode,
            line_spacing_multiplier,
        )

        doc.add_paragraph("Tabela 1 — Dados Cinéticos e Operacionais das Fontes da Seção").runs[0].bold = True

        sensors = report_data.get("sensors", [])
        if sensors:
            table = doc.add_table(rows=1, cols=6)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            set_ibge_table_borders(table)

            headers = ["Fonte ID", "Interseção / Local", "Velocidade", "Fluxo", "Ocupação", "Saturação"]
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
                vals = [
                    str(s.get("id", "")),
                    str(s.get("junction", "")),
                    str(s.get("measuredSpeed", "")),
                    str(s.get("measuredFlow", "")),
                    str(s.get("occupancyRate", "")),
                    str(s.get("saturationDegree", "")),
                ]
                for c_idx, val in enumerate(vals):
                    row_cells[c_idx].text = val
                    set_cell_margins(row_cells[c_idx], top=60, bottom=60, left=80, right=80)
                    p = row_cells[c_idx].paragraphs[0]
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx not in [0, 1] else WD_ALIGN_PARAGRAPH.LEFT
                    r = p.runs[0]
                    r.font.name = font_family
                    r.font.size = Pt(8)

            doc.add_paragraph("Fonte: Sistema SYNAPSE e fontes de monitoramento de tráfego (2026).").runs[0].font.size = Pt(7.5)
