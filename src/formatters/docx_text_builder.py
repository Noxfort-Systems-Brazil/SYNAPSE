# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import re
from typing import Any
from docx.shared import Pt, RGBColor


def add_formatted_text_to_paragraph(
    p: Any, text: str, font_size: float = 11.0, bold: bool = False, font_name: str = "Arial"
) -> None:
    """Splits text by ** (bold) and * (italic) to apply appropriate formatting runs inline."""
    if not text:
        return

    parts = text.split("**")
    is_bold_part = False
    for part in parts:
        if part:
            sub_parts = part.split("*")
            is_italic_sub = False
            for sub in sub_parts:
                if sub:
                    add_text_run_with_subscript_support(
                        p,
                        sub,
                        font_size=font_size,
                        is_bold=(is_bold_part or bold),
                        is_italic=is_italic_sub,
                        font_name=font_name,
                    )
                is_italic_sub = not is_italic_sub
        is_bold_part = not is_bold_part


def add_text_run_with_subscript_support(
    p: Any,
    text_segment: str,
    font_size: float = 11.0,
    is_bold: bool = False,
    is_italic: bool = False,
    font_name: str = "Arial",
) -> None:
    """
    Adds runs to paragraph p, detecting variable subscripts and applying native Word subscript.
    """
    pattern = (
        r"([a-zA-Zα-ωΑ-Ω\u0370-\u03ff\u1f00-\u1ffe\']+|"
        r"\b[a-zA-Zα-ωΑ-Ω\u0370-\u03ff\u1f00-\u1ffe]{1,50})_\{([^}]+)\}|"
        r"([a-zA-Zα-ωΑ-Ω\u0370-\u03ff\u1f00-\u1ffe\']+|"
        r"\b[a-zA-Zα-ωΑ-Ω\u0370-\u03ff\u1f00-\u1ffe]{1,50})_([a-zA-Z0-9α-ωΑ-Ω\u0370-\u03ff\u1f00-\u1ffe\-]+)|"
        r"\b(v)(real|limite|f)\b|\b(ρ)(jam)\b|\b(P)(95)\b"
    )

    last_idx = 0
    for match in re.finditer(pattern, text_segment):
        start, end = match.span()
        if start > last_idx:
            normal_part = text_segment[last_idx:start]
            r = p.add_run(normal_part)
            r.font.name = font_name
            r.font.size = Pt(font_size)
            r.font.color.rgb = RGBColor(0, 0, 0)
            if is_bold:
                r.bold = True
            if is_italic:
                r.italic = True

        g1 = match.group(1) or match.group(3)
        g2 = match.group(2) or match.group(4)
        if g1 and g2:
            base_var = g1
            sub_text = g2
        else:
            groups = [g for g in match.groups() if g is not None]
            if len(groups) >= 2:
                base_var = groups[-2]
                sub_text = groups[-1]
            else:
                base_var = text_segment[start:end]
                sub_text = ""

        # Add base variable
        r_base = p.add_run(base_var)
        r_base.font.name = font_name
        r_base.font.size = Pt(font_size)
        r_base.font.color.rgb = RGBColor(0, 0, 0)
        if is_bold:
            r_base.bold = True
        if is_italic:
            r_base.italic = True

        # Add subscript portion
        if sub_text:
            r_sub = p.add_run(sub_text)
            r_sub.font.name = font_name
            r_sub.font.size = Pt(font_size)
            r_sub.font.color.rgb = RGBColor(0, 0, 0)
            if is_bold:
                r_sub.bold = True
            if is_italic:
                r_sub.italic = True
            r_sub.font.subscript = True

        last_idx = end

    if last_idx < len(text_segment):
        rem_part = text_segment[last_idx:]
        r = p.add_run(rem_part)
        r.font.name = font_name
        r.font.size = Pt(font_size)
        r.font.color.rgb = RGBColor(0, 0, 0)
        if is_bold:
            r.bold = True
        if is_italic:
            r.italic = True
