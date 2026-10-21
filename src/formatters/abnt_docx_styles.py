# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
ABNT NBR 14724 & IBGE OpenXML Style Definitions for Microsoft Word (.docx).

SOLID: Single Responsibility Principle (SRP):
Encapsulates low-level OpenXML nodes, margins, borders, and typography formatting.
"""

from typing import Any
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn


def add_page_number(run):
    """Injects dynamic Word page number XML field."""
    fldChar1 = OxmlElement('w:fldChar')
    fldChar1.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText')
    instrText.set(qn('xml:space'), 'preserve')
    instrText.text = "PAGE"
    fldChar2 = OxmlElement('w:fldChar')
    fldChar2.set(qn('w:fldCharType'), 'separate')
    fldChar3 = OxmlElement('w:fldChar')
    fldChar3.set(qn('w:fldCharType'), 'end')

    r = run._r
    r.append(fldChar1)
    r.append(instrText)
    r.append(fldChar2)
    r.append(fldChar3)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Sets internal cell margins in twips (1 pt = 20 twips)."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def set_cell_background(cell, hex_color: str):
    """Sets background color of a table cell."""
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def set_ibge_table_borders(table):
    """
    Applies IBGE standard borders:
    - Top horizontal border
    - Bottom horizontal border of header
    - Bottom horizontal border of table
    - NO vertical borders
    """
    tblPr = table._tbl.tblPr
    borders_xml = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
        f'  <w:bottom w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
        f'  <w:insideH w:val="single" w:sz="4" w:space="0" w:color="D3D3D3"/>'
        f'  <w:insideV w:val="none"/>'
        f'  <w:left w:val="none"/>'
        f'  <w:right w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders_xml)


def apply_abnt_page_margins(doc: Document):
    """
    Configures ABNT NBR 14724 margins:
    Superior: 3,0 cm | Esquerda: 3,0 cm | Inferior: 2,0 cm | Direita: 2,0 cm
    """
    for section in doc.sections:
        section.top_margin = Cm(3.0)
        section.left_margin = Cm(3.0)
        section.bottom_margin = Cm(2.0)
        section.right_margin = Cm(2.0)
        section.header_distance = Cm(1.5)
        section.footer_distance = Cm(1.2)


def apply_abnt_normal_style(doc: Document, font_family: str, base_font_size_pt: float, line_spacing_multiplier: float, align_mode: Any):
    """Configures default document body style."""
    normal_style = doc.styles['Normal']
    normal_style.font.name = font_family
    normal_style.font.size = Pt(base_font_size_pt)
    normal_style.font.color.rgb = RGBColor(0, 0, 0)
    normal_style.paragraph_format.line_spacing = line_spacing_multiplier
    normal_style.paragraph_format.space_after = Pt(6)
    normal_style.paragraph_format.space_before = Pt(0)
    normal_style.paragraph_format.alignment = align_mode


def add_abnt_paragraph(doc: Document, text: str, font_family: str, base_font_size_pt: float, align_mode: Any, line_spacing_multiplier: float, bold_prefix: str = "", indent: bool = True):
    """Creates a paragraph with optional ABNT 1.25cm indent."""
    p = doc.add_paragraph()
    p.alignment = align_mode
    p.paragraph_format.line_spacing = line_spacing_multiplier
    p.paragraph_format.space_after = Pt(4)
    if indent:
        p.paragraph_format.first_line_indent = Cm(1.25)
    if bold_prefix:
        run_b = p.add_run(bold_prefix)
        run_b.bold = True
        run_b.font.name = font_family
        run_b.font.size = Pt(base_font_size_pt)
    run_t = p.add_run(text)
    run_t.font.name = font_family
    run_t.font.size = Pt(base_font_size_pt)
    return p


def add_abnt_heading_1(doc: Document, title: str, font_family: str, base_font_size_pt: float):
    """Creates a primary section title in uppercase bold (ABNT NBR 6024)."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.first_line_indent = Cm(0)
    run = p.add_run(title.upper())
    run.bold = True
    run.font.name = font_family
    run.font.size = Pt(base_font_size_pt + 1)
    return p


def add_abnt_heading_2(doc: Document, title: str, font_family: str, base_font_size_pt: float):
    """Creates a secondary section title in bold (ABNT NBR 6024)."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.first_line_indent = Cm(0)
    run = p.add_run(title)
    run.bold = True
    run.font.name = font_family
    run.font.size = Pt(base_font_size_pt)
    return p
