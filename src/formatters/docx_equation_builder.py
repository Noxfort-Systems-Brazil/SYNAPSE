# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import re
from typing import Any
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

from src.formatters.docx_text_builder import add_formatted_text_to_paragraph
from src.formatters.math_cleaner import clean_latex_math


class DocxEquationBuilder:
    """
    Renders centralized equations with ABNT NBR 14724 right-aligned tags into python-docx.
    Follows Single Responsibility Principle (SRP).
    """

    @staticmethod
    def render_equation(doc: Any, line_str: str, default_font_size: float = 11.0, font_name: str = "Arial") -> bool:
        """
        Parses equation string wrapped in $$ and renders it formatted with right-aligned tag.
        Returns True if line was processed as an equation, False otherwise.
        """
        if not (line_str.startswith("$$") and line_str.endswith("$$")):
            return False

        eq_raw = line_str[2:-2].strip()

        tag_match = re.search(r"\\tag\{([^}]+)\}", eq_raw) or re.search(r"\s*\(([A-Za-z0-9\.]+)\)\s*$", eq_raw)
        tag_str = ""
        if tag_match:
            tag_num = tag_match.group(1).strip()
            tag_str = f"({tag_num})" if not tag_num.startswith("(") else tag_num
            eq_raw = re.sub(r"\\tag\{[^}]+\}", "", eq_raw)
            eq_raw = re.sub(r"\s*\([A-Za-z0-9\.]+\)\s*$", "", eq_raw).strip()

        cleaned_eq = clean_latex_math(eq_raw)
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(8)

        if tag_str:
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            add_formatted_text_to_paragraph(
                p, f"      **{cleaned_eq}**", font_size=default_font_size, font_name=font_name
            )
            r_tag = p.add_run(f"\t\t{tag_str}")
            r_tag.bold = True
            r_tag.font.name = font_name
            r_tag.font.size = Pt(default_font_size)
        else:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_formatted_text_to_paragraph(
                p, f"**{cleaned_eq}**", font_size=default_font_size, font_name=font_name
            )

        return True
