# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import re
from typing import Any, Dict, Optional
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor

from src.formatters.docx_equation_builder import DocxEquationBuilder
from src.formatters.docx_image_builder import DocxImageBuilder
from src.formatters.docx_table_builder import render_markdown_table
from src.formatters.docx_text_builder import add_formatted_text_to_paragraph


def render_markdown_to_docx(
    doc: Any,
    markdown_text: str,
    default_font_size: float = 11.0,
    font_name: str = "Arial",
    context: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Renders standard Markdown text into a python-docx Document object.
    Orchestrates headers, code blocks, tables, math equations, images, and lists.
    Adheres to SOLID Single Responsibility Principle via specialized builders.
    """
    if context is None:
        context = {}
    if config is None:
        config = {}

    if not markdown_text:
        return

    lines = markdown_text.split("\n")
    i = 0
    in_code_block = False

    while i < len(lines):
        line = lines[i]
        line_str = line.strip()

        # 0. Handle Code Block Fences (```)
        if line_str.startswith("```"):
            in_code_block = not in_code_block
            i += 1
            continue

        if not line_str:
            i += 1
            continue

        # 0.1 Handle Page Break tags
        if any(tag in line_str.lower() for tag in ["<pagebreak>", "<!-- page break -->", "[page_break]"]):
            doc.add_page_break()
            cleaned_line = re.sub(r"(?i)<pagebreak>|<!-- page break -->|\[page_break\]", "", line_str).strip()
            if not cleaned_line:
                i += 1
                continue
            line_str = cleaned_line

        # 0.2 Handle Equation Block ($$ ... $$)
        if line_str.startswith("$$"):
            # Multi-line equation support
            eq_lines = [line_str]
            if not line_str.endswith("$$") or line_str == "$$":
                i += 1
                while i < len(lines):
                    sub_line = lines[i].strip()
                    eq_lines.append(sub_line)
                    if sub_line.endswith("$$"):
                        break
                    i += 1
                full_eq_str = " ".join(eq_lines)
            else:
                full_eq_str = line_str

            if DocxEquationBuilder.render_equation(doc, full_eq_str, default_font_size=default_font_size, font_name=font_name):
                i += 1
                continue

        # 0.3 Handle Markdown Images (![caption](src))
        if DocxImageBuilder.render_image(doc, line_str, font_name=font_name):
            i += 1
            continue

        # 0.4 Handle Markdown Tables (| Col1 | Col2 |)
        if line_str.startswith("|") and line_str.endswith("|"):
            table_lines = [line]
            i += 1
            while i < len(lines):
                next_l = lines[i].strip()
                if next_l.startswith("|") and next_l.endswith("|"):
                    table_lines.append(lines[i])
                    i += 1
                else:
                    break
            render_markdown_table(doc, table_lines, font_name=font_name, font_size=default_font_size - 1.5)
            continue

        # 1. Handle Headings (#, ##, ###, ####)
        if line_str.startswith("#"):
            heading_match = re.match(r"^(#{1,6})\s*(.+)$", line_str)
            if heading_match:
                level_count = len(heading_match.group(1))
                h_text = heading_match.group(2).strip()

                h_p = doc.add_paragraph()
                h_p.paragraph_format.keep_with_next = True

                if level_count == 1:
                    h_p.paragraph_format.space_before = Pt(16)
                    h_p.paragraph_format.space_after = Pt(6)
                    add_formatted_text_to_paragraph(h_p, h_text, font_size=default_font_size + 2.5, bold=True, font_name=font_name)
                elif level_count == 2:
                    h_p.paragraph_format.space_before = Pt(14)
                    h_p.paragraph_format.space_after = Pt(5)
                    add_formatted_text_to_paragraph(h_p, h_text, font_size=default_font_size + 1.5, bold=True, font_name=font_name)
                elif level_count == 3:
                    h_p.paragraph_format.space_before = Pt(10)
                    h_p.paragraph_format.space_after = Pt(4)
                    add_formatted_text_to_paragraph(h_p, h_text, font_size=default_font_size + 0.5, bold=True, font_name=font_name)
                else:
                    h_p.paragraph_format.space_before = Pt(8)
                    h_p.paragraph_format.space_after = Pt(3)
                    add_formatted_text_to_paragraph(h_p, h_text, font_size=default_font_size, bold=True, font_name=font_name)

                i += 1
                continue

        # 2. Handle Lists (- , * , 1. )
        bullet_match = re.match(r"^(\*|-|•)\s+(.+)$", line_str)
        num_match = re.match(r"^(\d+)[\.\)]\s+(.+)$", line_str)

        if bullet_match:
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            add_formatted_text_to_paragraph(p, bullet_match.group(2).strip(), font_size=default_font_size, font_name=font_name)
            i += 1
            continue

        if num_match:
            p = doc.add_paragraph(style="List Number")
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            add_formatted_text_to_paragraph(p, num_match.group(2).strip(), font_size=default_font_size, font_name=font_name)
            i += 1
            continue

        # 3. Handle Blockquotes / Callout Boxes (> ...)
        if line_str.startswith("> "):
            callout_text = line_str[2:].strip()
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            p.paragraph_format.left_indent = Cm(0.75)
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(4)
            add_formatted_text_to_paragraph(p, callout_text, font_size=default_font_size - 0.5, font_name=font_name)
            i += 1
            continue

        # 4. Handle Standard Narrative Paragraph (ABNT 1.25cm indent & 1.5 line spacing)
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = float(config.get("lineSpacing", 1.5)) if config else 1.5

        if len(line_str) > 80 and not line_str.startswith("**") and not line_str.startswith(">"):
            p.paragraph_format.first_line_indent = Cm(1.25)

        add_formatted_text_to_paragraph(p, line_str, font_size=default_font_size, font_name=font_name)
        i += 1
