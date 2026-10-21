# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Native Microsoft Word (.docx) Exporter in strict compliance with ABNT Standards:
- ABNT NBR 10719:2015 (Technical and scientific reports)
- ABNT NBR 14724:2011 (Presentation of formal reports: margins 3cm x 2cm, 1.5 spacing, 1.25cm indent)
- ABNT NBR 6024:2012 (Progressive numbering of sections)
- ABNT NBR 6023:2018 (Bibliographic and legislative references)
- IBGE Standard: Tables with open vertical borders and clean horizontal demarcations

SOLID Architecture:
- [SRP] Single Responsibility: Pure orchestrator assembling styles and sections into a .docx document.
- [OCP] Delegated section builders (abnt_docx_sections.py) and styles (abnt_docx_styles.py).
"""

import io
import os
from datetime import datetime
from typing import Dict, Any, Optional

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH

from src.formatters.abnt_docx_styles import (
    apply_abnt_page_margins,
    apply_abnt_normal_style,
)
from src.formatters.abnt_docx_sections import (
    render_header_and_cover,
    render_part_1_executive_summary,
    render_part_2_and_3_diagnosis_and_telemetry,
    render_part_4_and_5_math_and_xai,
    render_part_6_7_and_8_closing,
)
from src.utils.logging_setup import get_logger

logger = get_logger("Formatters.AbntDocxExporter")


class AbntDocxExporter:
    """
    Authoritative generator of official Municipal Traffic Audit Reports in Microsoft Word (.docx).
    """

    def generate(
        self,
        report_data: Dict[str, Any],
        typography_options: Optional[Dict[str, Any]] = None
    ) -> Document:
        """
        Builds a complete Document instance from report data and typography options.
        """
        opts = typography_options or {}
        font_family = opts.get("fontFamily", "Times New Roman")
        if font_family not in ["Times New Roman", "Arial"]:
            font_family = "Times New Roman"

        base_font_size_pt = float(opts.get("fontSize", 12))
        line_spacing_multiplier = float(opts.get("lineSpacing", 1.5))
        alignment_str = str(opts.get("alignment", "justify")).lower()
        align_mode = WD_ALIGN_PARAGRAPH.JUSTIFY if alignment_str == "justify" else WD_ALIGN_PARAGRAPH.LEFT

        doc = Document()

        # 1. Setup Margins and Default Typography Style (SRP: abnt_docx_styles)
        apply_abnt_page_margins(doc)
        apply_abnt_normal_style(doc, font_family, base_font_size_pt, line_spacing_multiplier, align_mode)

        timestamp_raw = report_data.get("timestamp", datetime.now().isoformat())
        try:
            dt_str = datetime.fromisoformat(timestamp_raw).strftime("%d/%m/%Y às %H:%M:%S")
        except Exception:
            dt_str = str(timestamp_raw)

        # 2. Render Document Sections (SRP: abnt_docx_sections)
        render_header_and_cover(doc, report_data, font_family, base_font_size_pt, dt_str)
        render_part_1_executive_summary(doc, report_data, font_family, base_font_size_pt, align_mode, line_spacing_multiplier)
        render_part_2_and_3_diagnosis_and_telemetry(doc, report_data, font_family, base_font_size_pt, align_mode, line_spacing_multiplier)
        render_part_4_and_5_math_and_xai(doc, report_data, font_family, base_font_size_pt, align_mode, line_spacing_multiplier)
        render_part_6_7_and_8_closing(doc, report_data, font_family, base_font_size_pt, align_mode, line_spacing_multiplier)

        return doc

    def export_to_bytes(
        self,
        report_data: Dict[str, Any],
        typography_options: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """Generates document and returns raw binary bytes."""
        doc = self.generate(report_data, typography_options)
        bio = io.BytesIO()
        doc.save(bio)
        bio.seek(0)
        return bio.getvalue()

    def export_to_file(
        self,
        report_data: Dict[str, Any],
        output_path: str,
        typography_options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generates document and writes directly to disk file."""
        doc = self.generate(report_data, typography_options)
        parent = os.path.dirname(output_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        doc.save(output_path)
        logger.info(f"Official Traffic Report exported to DOCX: {output_path}")
        return output_path
