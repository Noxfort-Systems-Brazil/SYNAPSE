# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import re
from typing import Any, List
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls
from docx.shared import Pt

from src.formatters.docx_text_builder import add_formatted_text_to_paragraph
from src.formatters.math_cleaner import clean_latex_math


def set_cell_background(cell, fill_hex: str):
    """Applies a background fill color to a docx table cell."""
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)


def render_markdown_table(doc, table_lines: List[str], font_name: str = "Arial", font_size: float = 9.0):
    """Parses markdown table lines and builds a styled graphic docx Table with 0.5pt borders and shaded header."""
    rows_data = []
    for line in table_lines:
        clean_l = line.strip()
        if re.match(r"^\|[\s:\|-]+\|?$", clean_l):
            continue
        cells = [c.replace("|", "").strip() for c in clean_l.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]
        if cells:
            rows_data.append(cells)

    if not rows_data:
        return

    num_rows = len(rows_data)
    num_cols = max(len(r) for r in rows_data)

    table = doc.add_table(rows=num_rows, cols=num_cols)
    table.style = "Table Grid"
    table.autofit = True

    # Thin borders for ABNT standard
    tblPr = table._element.xpath("w:tblPr")
    if tblPr:
        borders_xml = parse_xml(
            f'<w:tblBorders {nsdecls("w")}>\n'
            f'  <w:top w:val="single" w:sz="4" w:space="0" w:color="B0BEC5"/>\n'
            f'  <w:left w:val="single" w:sz="4" w:space="0" w:color="B0BEC5"/>\n'
            f'  <w:bottom w:val="single" w:sz="4" w:space="0" w:color="B0BEC5"/>\n'
            f'  <w:right w:val="single" w:sz="4" w:space="0" w:color="B0BEC5"/>\n'
            f'  <w:insideH w:val="single" w:sz="4" w:space="0" w:color="E0E0E0"/>\n'
            f'  <w:insideV w:val="single" w:sz="4" w:space="0" w:color="E0E0E0"/>\n'
            f"</w:tblBorders>"
        )
        tblPr[0].append(borders_xml)

    for row_idx, row in enumerate(rows_data):
        for col_idx, cell_text in enumerate(row):
            if col_idx < num_cols:
                cell = table.cell(row_idx, col_idx)
                p = cell.paragraphs[0]
                p.paragraph_format.space_before = Pt(3)
                p.paragraph_format.space_after = Pt(3)

                clean_cell_text = clean_latex_math(cell_text).replace("|", "").strip()

                # Align numeric or short ID columns to center, text columns to left
                clean_num_check = clean_cell_text.replace(".", "", 1).replace(",", "", 1).replace("%", "").strip()
                if clean_num_check.isdigit() or len(clean_cell_text) <= 8:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                else:
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT

                # Header row styling (#F2F2F2 fill)
                if row_idx == 0:
                    set_cell_background(cell, "F2F2F2")
                    tcPr = cell._element.get_or_add_tcPr()
                    header_border = parse_xml(
                        f'<w:tcBorders {nsdecls("w")}>\n'
                        f'  <w:bottom w:val="single" w:sz="8" w:space="0" w:color="222222"/>\n'
                        f"</w:tcBorders>"
                    )
                    tcPr.append(header_border)
                    add_formatted_text_to_paragraph(
                        p, clean_cell_text, font_size=font_size, bold=True, font_name=font_name
                    )
                else:
                    if row_idx % 2 == 1:
                        set_cell_background(cell, "F8FAFC")
                    add_formatted_text_to_paragraph(p, clean_cell_text, font_size=font_size, font_name=font_name)
