# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Equation Consistency Validation Rule (Class 09).

SOLID Compliance:
- [SRP] Exclusively audits mathematical integrity, presence of canonical tags (A.1 to A.5),
  completeness of Greek letters/symbols defined in text, and syntax correctness.
- Ensures all symbols declared in explanatory notes appear in corresponding formulas.
"""

import re
from typing import Any, Dict, List
from src.validation.exceptions import ReportViolation
from src.validation.base_rule import PostMarkdownRule


class EquationConsistencyRule(PostMarkdownRule):
    """Rule 9.1: Validates that every variable/Greek symbol explained in text appears in formula."""

    REQUIRED_TAGS = ["2.2.1", "2.2.2", "2.2.3", "2.2.4", "2.2.5"]

    GREEK_LETTERS = {
        "ρ": [r"\rho", "ρ"],
        "λ": [r"\lambda", "λ"],
        "α": [r"\alpha", "α"],
        "Δ": [r"\Delta", "Δ"],
    }

    def validate_post(
        self, markdown_text: str, report_data: Dict[str, Any], context: Any = None
    ) -> List[ReportViolation]:
        violations: List[ReportViolation] = []
        if not markdown_text:
            return violations

        # 1. Verify presence of all canonical equation tags (support 2.2.x or A.x)
        is_legacy_tag = any(f"A.{i}" in markdown_text for i in range(1, 6)) and not any("2.2.1" in markdown_text for _ in [1])
        tags_to_check = ["A.1", "A.2", "A.3", "A.4", "A.5"] if is_legacy_tag else self.REQUIRED_TAGS

        for tag in tags_to_check:
            if tag not in markdown_text:
                violations.append(
                    ReportViolation(
                        error_class=9,
                        title="Equação Canônica Ausente no Relatório",
                        message=f"A Equação {tag} é obrigatória e não foi identificada.",
                        section="Seção de Equações",
                    )
                )

        # 2. Extract equation blocks (#### 2.2.x or #### A.x ... up to next #### or section)
        blocks = re.findall(r"(####\s*(?:2\.2\.|A\.)[1-5][\s\S]*?)(?=####\s*(?:2\.2\.|A\.)[1-5]|##\s|\Z)", markdown_text)
        for block in blocks:
            tag_m = re.search(r"(?:2\.2\.|A\.)([1-5])", block)
            if not tag_m:
                continue
            idx = tag_m.group(1)
            tag = f"2.2.{idx}" if "2.2." in block else f"A.{idx}"

            formula_m = re.search(r"\$\$([\s\S]*?)\$\$", block)
            formula = formula_m.group(1).strip() if formula_m else ""

            # Check Greek symbols defined in parameter explanation
            for char, patterns in self.GREEK_LETTERS.items():
                if f"**{char}**" in block or f"**{char}_" in block or f"**\\{char}" in block:
                    found = any(p in formula for p in patterns)
                    if not found:
                        violations.append(
                            ReportViolation(
                                error_class=9,
                                title="Símbolo Grego Definido Ausente na Equação",
                                message=f"O símbolo grego '{char}' foi definido na explicação de {tag}, mas não consta na fórmula.",
                                section=f"Equação {tag}",
                            )
                        )

            # Equation 3: must contain square root of d_model
            if idx == "3":
                if not (r"\sqrt" in formula or "√" in formula or "sqrt" in formula.lower()):
                    violations.append(
                        ReportViolation(
                            error_class=9,
                            title=f"Fator de Escala Ausente na Equação {tag}",
                            message=f"A Equação {tag} deve conter a raiz quadrada da dimensão latente (√d_model).",
                            section=f"Equação {tag}",
                        )
                    )

            # Equation 5: must contain exponential damping e^(-λΔt) and no broken braces
            if idx == "5":
                if re.search(r"\{t-1\}\}", formula) or "a t-1}" in formula or "a_{t-1}}" in formula:
                    violations.append(
                        ReportViolation(
                            error_class=9,
                            title=f"Sintaxe Inválida na Equação {tag}",
                            message=f"Chave sobressalente ou formatação corrompida identificada na Equação {tag}.",
                            section=f"Equação {tag}",
                        )
                    )
                has_exp = (
                    r"e^{-\lambda" in formula
                    or r"e^{-\lambda \Delta t}" in formula
                    or "exp(-λ" in formula
                    or "e^(-λ" in formula
                    or "e^-λ" in formula
                )
                if not has_exp:
                    violations.append(
                        ReportViolation(
                            error_class=9,
                            title=f"Decaimento Exponencial Ausente na Equação {tag}",
                            message=f"A Equação {tag} deve utilizar formulação de decaimento e^(-λΔt).",
                            section=f"Equação {tag}",
                        )
                    )
            # Verify no orphan braces exist in explanatory prose or formula
            prose = re.sub(r"\$\$[\s\S]*?\$\$", "", block)
            temp_prose = prose
            for _ in range(5):
                cleaned_braces = re.sub(r"\{[^{}]*\}", "", temp_prose)
                if cleaned_braces == temp_prose:
                    break
                temp_prose = cleaned_braces

            if "{" in temp_prose or "}" in temp_prose or "a t-1}" in prose:
                violations.append(
                    ReportViolation(
                        error_class=9,
                        title="Chave Órfã no Texto Explicativo da Equação",
                        message=f"Chave sobressalente identificada na explicação da equação {tag}.",
                        section=f"Equação {tag}",
                    )
                )

        return violations
