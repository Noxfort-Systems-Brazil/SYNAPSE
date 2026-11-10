# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Any, Dict, List
from src.xai.report_block_base import ReportBlockBase
from src.xai.canonical_equations import CanonicalReportEquations


class ReportEquationsRenderer(ReportBlockBase):
    """
    Renders formal mathematical equations, parameters, and completeness axioms for XAI methodologies.
    Uses reviewed canonical fixed equation definitions to guarantee consistency.
    """

    def render(self, lines: List[str], block: Dict[str, Any], context: Dict[str, Any]) -> None:
        title_key = block.get("title_key", "")
        if title_key and self._t(title_key):
            lines.append(self._t(title_key))
        else:
            lines.append("### 2.2 Memorial de Cálculo e Formulações Matemáticas de Percepção")

        intro_key = block.get("intro_key", "")
        if intro_key and self._t(intro_key):
            lines.append(self._t(intro_key))
            lines.append("")
        else:
            lines.append("O motor **SYNAPSE v2.0 Enterprise** fundamenta suas estimativas de estado e explicabilidade em formulações matemáticas determinísticas baseadas nas leis fundamentais de tráfego (LWR/HCM) e métodos de interpretabilidade neural:")
            lines.append("")

        equations = CanonicalReportEquations.EQUATIONS
        for eq in equations:
            lines.append(eq["title"])
            lines.append(eq["desc"])
            lines.append(eq["formula"])
            lines.append(eq["params"])

            if eq.get("completeness_formula"):
                lines.append("")
                if eq.get("completeness_axiom"):
                    lines.append(eq["completeness_axiom"])
                lines.append(eq["completeness_formula"])
                if eq.get("completeness_desc"):
                    lines.append(eq["completeness_desc"])

            lines.append("")
