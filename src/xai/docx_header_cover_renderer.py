# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
DOCX Institutional Cover, Header, Footer and Ementa Renderer.

SOLID Design:
- Single Responsibility Principle (SRP): Encapsulates only the construction of the formal cover,
  institutional titles, primary section running header, ABNT footer, date/city, legal ementa,
  and operational environment identification table (MetadataBlock).
- Clean Architecture / DDD: Operates directly on OfficialReportData aggregate.
- CARINA_CORE Pattern Parity: Adheres to CARINA HeaderBlock, TitleBlock and MetadataBlock standards.
"""

import os
from datetime import datetime
from typing import Dict, Any, Union
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

from src.domain.official_report import OfficialReportData
from src.xai.xai_template_repository import XaiTemplateRepository
from src.formatters.abnt_docx_styles import (
    add_page_number,
    set_ibge_table_borders,
    set_cell_margins,
    set_cell_background,
)


class DocxHeaderCoverRenderer:
    """
    Renders formal cover, running headers, running footers, and ementa
    in compliance with ABNT NBR 10719:2015 and municipal reporting standards (CARINA_CORE parity).
    """

    MONTHS_PT = [
        "janeiro", "fevereiro", "março", "abril", "maio", "junho",
        "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
    ]

    def render(
        self,
        doc: Document,
        report_data: Union[OfficialReportData, Dict[str, Any]],
        font_family: str,
        base_font_size_pt: float,
        dt_str: str,
    ) -> None:
        """Renders formal cover and institutional header."""
        r = OfficialReportData.from_dict(report_data) if not isinstance(report_data, OfficialReportData) else report_data
        city_hall = (report_data.get("cityHall") or report_data.get("city_hall") or r.city_hall) if isinstance(report_data, dict) else r.city_hall
        department = (report_data.get("department") or r.department) if isinstance(report_data, dict) else r.department
        protocol = r.protocol
        process_num = r.process_number
        system_ver = r.system_version
        authority = r.authority_name or "(A preencher pelo Responsável Técnico)"
        authority_role = r.authority_role or "Engenheiro de Tráfego / Responsável Técnico"
        registration = r.registration_number or "CREA / ART a vincular"

        loc = report_data.get("location", {}) if isinstance(report_data, dict) else {}
        corridor = loc.get("corridorName") or "Corredor Arterial Central — Eixo Norte-Sul"
        jurisdiction = loc.get("jurisdiction") or "Circunscrição Municipal"

        # 1. Header (Primary section running header with right-aligned page number)
        primary_section = doc.sections[0]
        header = primary_section.header
        header_p = header.paragraphs[0]
        header_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        header_run = header_p.add_run(f"{protocol} • Processo: {process_num} | Pág. ")
        header_run.font.name = font_family
        header_run.font.size = Pt(9)
        header_run.font.color.rgb = RGBColor(100, 100, 100)
        add_page_number(header_run)

        # 2. Footer (ABNT NBR 10719 standard compliance disclaimer)
        footer = primary_section.footer
        footer_p = footer.paragraphs[0]
        footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cert_hash = str(report_data.get("digitalCertification", "AUTENTICADO-ICP-BRASIL"))[:40]
        footer_run = footer_p.add_run(
            f"SYNAPSE Zero-Trust Sensor Fusion • ABNT NBR 10719:2015 • CTB Art. 24 • Hash: {cert_hash}..."
        )
        footer_run.font.name = font_family
        footer_run.font.size = Pt(8)
        footer_run.font.italic = True
        footer_run.font.color.rgb = RGBColor(120, 120, 120)

        # Operational Draft Notice Banner
        templates = report_data.get("templates") if isinstance(report_data, dict) else None
        lang = str(report_data.get("language", "pt_br") if isinstance(report_data, dict) else "pt_br").lower()
        if not templates:
            templates = XaiTemplateRepository.get_templates_for_language(lang)

        banner_p = doc.add_paragraph()
        banner_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        banner_p.paragraph_format.space_before = Pt(0)
        banner_p.paragraph_format.space_after = Pt(4)
        raw_banner = templates.get("cover_notice", "[ Documento gerado automaticamente — rascunho técnico até validação ]")
        clean_banner = raw_banner.replace("> **Aviso Operacional:** *", "").replace("> **Operational Notice:** *", "").replace("> **Aviso Operacional:** *", "").rstrip("*").strip()
        if not clean_banner.startswith("["):
            clean_banner = f"[ {clean_banner} ]"
        r_banner = banner_p.add_run(clean_banner)
        r_banner.font.name = font_family
        r_banner.font.size = Pt(8.5)
        r_banner.font.italic = True
        r_banner.font.color.rgb = RGBColor(128, 0, 0)

        # 3. Institutional Title block (CARINA HeaderBlock parity: 2-column table if logo present)
        logo_path = report_data.get("logo_path") or (report_data.get("municipal_config", {}).get("logo_path") if isinstance(report_data, dict) else None)
        valid_logo = bool(logo_path and os.path.exists(str(logo_path)) and os.path.splitext(str(logo_path).lower())[1] in [".png", ".jpg", ".jpeg"])
        if valid_logo:
            try:
                hdr_tbl = doc.add_table(rows=1, cols=2)
                hdr_tbl.autofit = False
                hdr_tbl.columns[0].width = Cm(3.0)
                hdr_tbl.columns[1].width = Cm(14.0)

                cell_logo = hdr_tbl.cell(0, 0)
                cell_logo.width = Cm(3.0)
                p_logo = cell_logo.paragraphs[0]
                p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p_logo.add_run().add_picture(str(logo_path), width=Cm(2.5))

                cell_text = hdr_tbl.cell(0, 1)
                cell_text.width = Cm(14.0)
                title_p = cell_text.paragraphs[0]
            except Exception:
                title_p = doc.add_paragraph()
        else:
            title_p = doc.add_paragraph()

        title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_p.paragraph_format.space_after = Pt(2)
        r_gov = title_p.add_run(f"{city_hall}\n{department}\n")
        r_gov.bold = True
        r_gov.font.name = font_family
        r_gov.font.size = Pt(11)

        superintendence = templates.get("cover_superintendence", "**SUPERINTENDÊNCIA DE ENGENHARIA DE TRÁFEGO E OPERAÇÃO VIÁRIA**").replace("**", "")
        gw_desc = templates.get("cover_gateway_desc", "Gateway de Percepção Inteligente e Fusão Neural de Sensores")
        sys_label = system_ver if "SYNAPSE" in system_ver else f"SYNAPSE {system_ver}"
        r_sub = title_p.add_run(f"{superintendence}\n{gw_desc.upper()} ({sys_label})")
        r_sub.font.name = font_family
        r_sub.font.size = Pt(9.5)
        r_sub.font.color.rgb = RGBColor(70, 70, 70)

        div_p = doc.add_paragraph()
        div_p.paragraph_format.space_after = Pt(10)
        r_div = div_p.add_run("―" * 62)
        r_div.font.size = Pt(8)
        r_div.font.color.rgb = RGBColor(160, 160, 160)

        # 4. Official Date & City (Right-aligned, CARINA TitleBlock parity)
        try:
            timestamp_raw = report_data.get("timestamp", datetime.now().isoformat()) if isinstance(report_data, dict) else datetime.now().isoformat()
            dt = datetime.fromisoformat(str(timestamp_raw))
        except Exception:
            dt = datetime.now()
        months = templates.get("months_names", self.MONTHS_PT)
        month_str = months[dt.month - 1]
        city = report_data.get("city", "São Paulo") if isinstance(report_data, dict) else "São Paulo"
        state_uf = report_data.get("state_uf", "SP") if isinstance(report_data, dict) else "SP"
        if "en" in lang:
            official_date_str = f"{city} - {state_uf}, {month_str} {dt.day}, {dt.year}"
        else:
            official_date_str = f"{city} - {state_uf}, {dt.day} de {month_str} de {dt.year}"

        p_date = doc.add_paragraph()
        p_date.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_date.paragraph_format.space_before = Pt(4)
        p_date.paragraph_format.space_after = Pt(8)
        run_date = p_date.add_run(official_date_str)
        run_date.font.size = Pt(10)
        run_date.italic = True
        run_date.font.name = font_family
        run_date.font.color.rgb = RGBColor(60, 60, 60)

        # 5. Main Title with Protocol Number (CARINA TitleBlock parity)
        main_title = doc.add_paragraph()
        main_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        main_title.paragraph_format.space_before = Pt(4)
        main_title.paragraph_format.space_after = Pt(6)
        main_title_tpl = templates.get("cover_report_title", "LAUDO TÉCNICO DE AUDITORIA DE TRÁFEGO — RELATÓRIO EXPLICATIVO DO SYNAPSE (XAI) Nº {protocol}").replace("# ", "")
        r_main = main_title.add_run(main_title_tpl.replace("{protocol}", protocol))
        r_main.bold = True
        r_main.font.size = Pt(13)
        r_main.font.name = font_family

        sub_desc = doc.add_paragraph()
        sub_desc.alignment = WD_ALIGN_PARAGRAPH.CENTER
        sub_desc.paragraph_format.space_after = Pt(10)
        r_desc = sub_desc.add_run(
            f"Processo Administrativo: {process_num} • Horário de Referência: {dt_str} • Sistema: {system_ver}"
        )
        r_desc.font.size = Pt(9.5)
        r_desc.font.italic = True
        r_desc.font.name = font_family

        # 6. Official Ementa (Right-indented block, CARINA TitleBlock parity)
        p_ementa = doc.add_paragraph()
        p_ementa.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_ementa.paragraph_format.left_indent = Pt(180)  # Indent to the right half
        p_ementa.paragraph_format.space_before = Pt(4)
        p_ementa.paragraph_format.space_after = Pt(14)
        raw_ementa = templates.get("cover_ementa", "Auditoria de Inteligência Artificial, Explicabilidade Algorítmica (XAI), Salvaguardas Operacionais e Avaliação de Desempenho Operacional da Malha Viária Urbana.")
        clean_ementa = raw_ementa.replace("> **Assunto / Ementa:** *", "Assunto / Ementa: ").replace("> **Subject / Summary:** *", "Subject / Summary: ").replace("> **Asunto / Resumen:** *", "Asunto / Resumen: ").rstrip("*").strip()
        r_ementa = p_ementa.add_run(clean_ementa)
        r_ementa.font.name = font_family
        r_ementa.font.size = Pt(9.5)
        r_ementa.font.italic = True
        r_ementa.font.color.rgb = RGBColor(60, 60, 60)

        # 7. Operational Environment & Identification Table (CARINA MetadataBlock parity)
        p_meta_title = doc.add_paragraph()
        p_meta_title.paragraph_format.space_before = Pt(8)
        p_meta_title.paragraph_format.space_after = Pt(4)
        id_table_title = templates.get("cover_id_table_title", "Quadro de Identificação do Sistema e Contexto Operacional").replace("### ", "")
        r_meta_title = p_meta_title.add_run(id_table_title)
        r_meta_title.bold = True
        r_meta_title.font.name = font_family
        r_meta_title.font.size = Pt(10)

        num_sensors = len(report_data.get("sensors", [])) if isinstance(report_data, dict) else 4
        num_sensors = num_sensors or 4
        total_samples = num_sensors * 120
        r_sys = templates.get("cover_row_sys_id", "Identificador do Sistema:")
        r_corr = templates.get("cover_row_corridor", "Corredor Monitorado:")
        r_per = templates.get("cover_row_period", "Período e Horário dos Dados:")
        v_per = templates.get("cover_period_val", f"Referência em `{dt_str}` (Janela de 120s • Taxa contínua de 1,0s • Fuso UTC-03:00)").replace("`", "").replace("{dt_str}", dt_str)
        r_samp = templates.get("cover_row_samples", "Volume de Amostras:")
        v_samp = templates.get("cover_samples_val", f"{total_samples} leituras ({num_sensors} fontes x 120 ciclos a 1,0 Hz)").replace("{total_eval}", str(total_samples)).replace("{num_sources}", str(num_sensors))
        r_obj = templates.get("cover_row_objective", "Objetivo da Estimativa:")
        v_obj = templates.get("cover_row_objective_val", "Reconstrução contínua da velocidade (usando medições pontuais como aproximação da velocidade espacial), densidade e saturação da malha viária")
        r_proc = templates.get("cover_row_process", "Processo Administrativo:")
        r_prot = templates.get("cover_row_protocol", "Protocolo de Emissão:")
        r_sup = templates.get("cover_row_supervisor", "Supervisão / Responsável Técnico:")

        metadata_rows = [
            (f"{r_sys}:" if not r_sys.endswith(":") else r_sys, sys_label),
            (f"{r_corr}:" if not r_corr.endswith(":") else r_corr, f"{corridor} ({jurisdiction})"),
            (f"{r_per}:" if not r_per.endswith(":") else r_per, v_per),
            (f"{r_samp}:" if not r_samp.endswith(":") else r_samp, v_samp),
            (f"{r_obj}:" if not r_obj.endswith(":") else r_obj, v_obj),
            (f"{r_proc}:" if not r_proc.endswith(":") else r_proc, process_num),
            (f"{r_prot}:" if not r_prot.endswith(":") else r_prot, protocol),
            (f"{r_sup}:" if not r_sup.endswith(":") else r_sup, f"{authority} ({authority_role} — {registration})"),
        ]

        meta_table = doc.add_table(rows=len(metadata_rows), cols=2)
        meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_ibge_table_borders(meta_table)

        for idx, (label, val) in enumerate(metadata_rows):
            row_cells = meta_table.rows[idx].cells
            cell_lbl, cell_val = row_cells[0], row_cells[1]

            cell_lbl.text = label
            cell_val.text = val

            set_cell_margins(cell_lbl, top=40, bottom=40, left=60, right=60)
            set_cell_margins(cell_val, top=40, bottom=40, left=60, right=60)

            p_lbl = cell_lbl.paragraphs[0]
            p_lbl.alignment = WD_ALIGN_PARAGRAPH.LEFT
            r_lbl = p_lbl.runs[0]
            r_lbl.bold = True
            r_lbl.font.name = font_family
            r_lbl.font.size = Pt(8.5)

            p_val = cell_val.paragraphs[0]
            p_val.alignment = WD_ALIGN_PARAGRAPH.LEFT
            r_val = p_val.runs[0]
            r_val.font.name = font_family
            r_val.font.size = Pt(8.5)

        doc.add_paragraph().paragraph_format.space_after = Pt(8)
