# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import re


def clean_latex_math(eq: str) -> str:
    """
    Cleans LaTeX mathematical syntax for clean Word document rendering.
    Processes:
    - Fractions \\frac{num}{den} into num / (den) or num / den
    - Subscript variables (v_{real} -> v_real, P_{95} -> P_95, F_{ideal} -> F_ideal)
    - Stripping \\mathbf, \\text, \\tag and LaTeX escape characters
    """
    if not eq:
        return ""

    eq = eq.replace("$$", "").replace("$", "").strip()

    # Clean \\tag{...} and \\mathbf{...}
    eq = re.sub(r"\\tag\{[^{}]+\}", "", eq)
    eq = re.sub(r"\\mathbf\s*\{", "", eq)

    # Clean \\left and \\right delimiters and escaped parens
    eq = eq.replace(r"\\left(", "(").replace(r"\\right)", ")")
    eq = eq.replace(r"\left(", "(").replace(r"\right)", ")")
    eq = eq.replace(r"\\left[", "[").replace(r"\\right]", "]")
    eq = eq.replace(r"\left[", "[").replace(r"\right]", "]")
    eq = eq.replace(r"\\left\{", "{").replace(r"\\right\}", "}")
    eq = eq.replace(r"\left\{", "{").replace(r"\right\}", "}")
    eq = eq.replace(r"\\left", "").replace(r"\\right", "")
    eq = eq.replace(r"\left", "").replace(r"\right", "")
    eq = eq.replace(r"\(", "(").replace(r"\)", ")")
    eq = eq.replace(r"\[", "[").replace(r"\]", "]")

    # Clean \\text{...}
    eq = re.sub(r"\\text\{([^{}]+)\}", r"\1", eq)

    # Process \\frac{num}{den} robustly
    def _format_frac(m):
        num = m.group(1).strip()
        den = m.group(2).strip()
        if r"\times" in den or r"\cdot" in den or "*" in den or "+" in den or "-" in den or " " in den or "×" in den:
            return f"{num} / ({den})"
        return f"{num} / {den}"

    frac_pattern = re.compile(r"\\frac\{((?:[^{}]|\{[^{}]*\})+)\}\{((?:[^{}]|\{[^{}]*\})+)\}")
    max_loops = 5
    while r"\frac" in eq and max_loops > 0:
        max_loops -= 1
        new_eq = frac_pattern.sub(_format_frac, eq)
        if new_eq == eq:
            eq = re.sub(r"\\frac\{([^}]+)\}\{([^}]+)\}", r"\1 / \2", eq)
            break
        eq = new_eq

    # Clean square roots \sqrt{...} and \sqrt
    eq = re.sub(r"\\sqrt\{((?:[^{}]|\{[^{}]*\})+)\}", r"√(\1)", eq)
    eq = eq.replace(r"\sqrt", "√")

    # Clean subscripts (including negative offsets like t-1)
    eq = re.sub(r"([a-zA-Z0-9α-ωΑ-Ω]+)_\{([a-zA-Z0-9_\-]+)\}", r"\1_\2", eq)
    eq = re.sub(r"([a-zA-Z0-9α-ωΑ-Ω]+)_([a-zA-Z0-9\-]+)", r"\1_\2", eq)

    # Clean latex multiplication & math operators
    eq = eq.replace(r"\times", "×").replace(r"\cdot", "·")
    eq = eq.replace(r"\alpha", "α").replace(r"\tau", "τ").replace(r"\lambda", "λ")
    eq = eq.replace(r"\int", "∫").replace(r"\partial", "∂")
    eq = eq.replace(r"\parallel", "∥").replace(r"\in", "∈")
    eq = eq.replace(r"\sum_{a}", "∑ₐ").replace(r"\sum_{", "∑_").replace(r"\sum", "∑")
    eq = eq.replace(r"\log", "log").replace(r"\exp", "exp").replace(r"\softmax", "softmax")
    eq = eq.replace(r"\Delta", "Δ").replace(r"\delta", "δ")
    eq = eq.replace(r"\pi", "π").replace(r"\rho", "ρ")
    eq = eq.replace(r"\%", "%")
    eq = eq.replace(r"\infty", "∞").replace(r"\approx", "≈")
    eq = eq.replace(r"\leq", "≤").replace(r"\geq", "≥").replace(r"\neq", "≠")

    # Clean any remaining unknown LaTeX keywords or backslashes
    eq = re.sub(r"\\[a-zA-Z]+", "", eq)
    eq = eq.replace("{", "").replace("}", "").replace("\\", "")

    return re.sub(r"\s+", " ", eq).strip()
