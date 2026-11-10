# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Textual and Stylistic Post-Markdown Validation Rules.
Validates placeholders, internal leaks, prohibited language, and grammar.
"""

import re
from typing import Any, Dict, List, Optional
from src.validation.exceptions import ReportViolation
from src.validation.base_rule import PostMarkdownRule


class TemplateLeakRule(PostMarkdownRule):
    """Rule 1: Detects unrendered template placeholders, enum leaks, None or NaN."""

    INTERNAL_LEAKS = [
        "SourceType.",
        "PI_DVAE_CORRECTOR",
        "KSE_DEAD_RECKONING",
        "DATA_PAYLOAD",
        "Enum.",
    ]

    def validate_post(self, markdown_text: str, report_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[ReportViolation]:
        violations: List[ReportViolation] = []
        if not markdown_text:
            return [
                ReportViolation(
                    error_class=1,
                    title="Documento Vazio",
                    message="O texto Markdown do relatório gerado está vazio.",
                    section="Documento Completo",
                )
            ]

        non_math = re.sub(r"\$\$.*?\$\$", "", markdown_text, flags=re.DOTALL)
        non_math = re.sub(r"\$[^\$]+?\$", "", non_math)

        placeholders = re.findall(r"(?<![\\])\{([a-zA-Z][a-zA-Z0-9_]*)\}", non_math)
        if placeholders:
            violations.append(
                ReportViolation(
                    error_class=1,
                    title="Placeholders Não Renderizados",
                    message=f"Placeholders de template não preenchidos encontrados no texto: {', '.join(set(placeholders))}",
                    section="Documento Completo",
                )
            )

        for leak in self.INTERNAL_LEAKS:
            if leak in non_math:
                violations.append(
                    ReportViolation(
                        error_class=1,
                        title="Vazamento de Nome Interno / Enum",
                        message=f"Termo interno ou enum '{leak}' vazou para o texto público do relatório.",
                        section="Documento Completo",
                    )
                )

        if re.search(r"\bNone\b", non_math):
            violations.append(
                ReportViolation(
                    error_class=1,
                    title="Valor 'None' Não Tratado",
                    message="Literal 'None' encontrado no corpo do documento.",
                    section="Documento Completo",
                )
            )
        if re.search(r"\bnan\b", non_math, flags=re.IGNORECASE):
            violations.append(
                ReportViolation(
                    error_class=1,
                    title="Valor 'NaN' Não Tratado",
                    message="Valor numérico inválido 'NaN' encontrado no texto.",
                    section="Documento Completo",
                )
            )

        return violations


class ProhibitedTermsRule(PostMarkdownRule):
    """Rule 11: Enforces ban on absolute, misleading, or overreaching terms."""

    PROHIBITED_TERMS = [
        "possuem fé pública",
        "com fé pública",
        "laudo pericial",
        "100% fidedigno",
        "ausência de viés",
        "ausência de viés comprovada",
        "garante que 100%",
        "comprova a ausência",
        "atribuição causal",
        "peso causal",
        "caixa-preta",
        "hidrodinâmica",
        "normativo",
        "normativa",
        "normativos",
        "normativas",
        "canônico",
        "canônica",
        "canônicos",
        "canônicas",
        "canonico",
        "canonica",
        "canonicos",
        "canonicas",
        "oficial",
        "oficiais",
    ]

    def validate_post(self, markdown_text: str, report_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[ReportViolation]:
        violations: List[ReportViolation] = []
        non_math = re.sub(r"\$\$.*?\$\$", "", markdown_text, flags=re.DOTALL)
        non_math = re.sub(r"\$[^\$]+?\$", "", non_math)

        for term in self.PROHIBITED_TERMS:
            pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
            for line in non_math.splitlines():
                if pattern.search(line):
                    if "fé pública" in term.lower() and "sem fé pública" in line.lower():
                        continue
                    violations.append(
                        ReportViolation(
                            error_class=11,
                            title="Linguagem Absoluta Proibida",
                            message=f"Uso do termo proibido '{term}' detectado na linha: '{line.strip()[:80]}...'",
                            section="Linguagem do Relatório",
                        )
                    )
        return violations


class ThresholdsTableRule(PostMarkdownRule):
    """Rule 3: Enforces presence of speed and saturation thresholds table."""

    def validate_post(self, markdown_text: str, report_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[ReportViolation]:
        violations: List[ReportViolation] = []
        has_thresholds = any(
            kw in markdown_text
            for kw in [
                "Limiares", "Nível Operacional", "Saturação",
                "Thresholds", "Operational Level", "Saturation",
                "Umbrales", "Nivel Operacional", "Saturación"
            ]
        )
        if not has_thresholds:
            violations.append(
                ReportViolation(
                    error_class=3,
                    title="Tabela de Limiares Ausente",
                    message="O relatório deve imprimir os limiares de classificação de velocidade e saturação para transparência.",
                    section="Metodologia / Resumo",
                )
            )
        return violations


class ParametricInterdependenceRule(PostMarkdownRule):
    """Rule 6: Enforces explanatory notice when model-derived variables are present."""

    def validate_post(self, markdown_text: str, report_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[ReportViolation]:
        violations: List[ReportViolation] = []
        has_derived = (
            "[Derivado por Modelo]" in markdown_text
            or "[derivado por modelo]" in markdown_text.lower()
            or "[model-derived]" in markdown_text.lower()
        )
        if has_derived:
            if not any(kw in markdown_text.lower() for kw in ["interdependência", "interdependence", "interdependencia"]):
                violations.append(
                    ReportViolation(
                        error_class=6,
                        title="Aviso de Interdependência Ausente",
                        message="O relatório contém variáveis derivadas por modelo, mas omitiu o aviso explicativo de interdependência paramétrica na Seção 3.",
                        section="Seção 3 (Explicabilidade)",
                    )
                )
        return violations


class GrammarAndFormattingRule(PostMarkdownRule):
    """Rule 12: Enforces formatting standards, plural agreement, duplicate words, and label redundancy."""

    @classmethod
    def validate_redundancy(cls, markdown_text: str) -> List[ReportViolation]:
        violations: List[ReportViolation] = []
        redundancy_patterns = [
            (
                r"autoencoder\s+convolucional\s+(?:de\s+)?Filtro\s+de\s+Ru[íi]do",
                "autoencoder convolucional Filtro de Ruído Convolucional",
            ),
            (
                r"estimador\s+cinem[áa]tico\s+Estimador\s+Cinem[áa]tico",
                "estimador cinemático Estimador Cinemático",
            ),
            (
                r"quarentena\s+(?:Zero-Trust\s+)?Quarentena",
                "quarentena Quarentena",
            ),
            (
                r"\b([A-Za-zÀ-ÖØ-öø-ÿ]{5,}\s+[A-Za-zÀ-ÖØ-öø-ÿ]{5,})\s+\1\b",
                "expressão de duas palavras consecutivas duplicada",
            ),
        ]
        for pat, desc in redundancy_patterns:
            matches = re.finditer(pat, markdown_text, flags=re.IGNORECASE)
            for m in matches:
                matched_snippet = m.group(0)
                violations.append(
                    ReportViolation(
                        error_class=12,
                        title="Redundância Nominal de Rótulo",
                        message=f"Rótulo seguido da própria descrição nominal detectado: '{matched_snippet}' ({desc}).",
                        section="Forma e Gramática",
                    )
                )
        return violations

    def validate_post(self, markdown_text: str, report_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[ReportViolation]:
        violations = self.validate_redundancy(markdown_text)
        non_math = re.sub(r"\$\$.*?\$\$", "", markdown_text, flags=re.DOTALL)
        non_math = re.sub(r"\$[^\$]+?\$", "", non_math)

        dup_matches = re.finditer(r"\b([a-zA-ZáéíóúÁÉÍÓÚçÇãõÃÕ]{4,})\s+\1\b", non_math, flags=re.IGNORECASE)
        for m in dup_matches:
            dup_word = m.group(1)
            if dup_word.lower() not in ["para", "como", "mais"]:
                violations.append(
                    ReportViolation(
                        error_class=12,
                        title="Palavra Consecutiva Duplicada",
                        message=f"Duplicação consecutiva da palavra '{dup_word}' detectada no texto.",
                        section="Forma e Gramática",
                    )
                )

        lang = str(report_data.get("language", "pt_br")).lower()
        if "en" not in lang:
            dot_decimal_matches = re.findall(r"\b\d+\.\d+\s*(?:km/h|veíc/h|%)\b", non_math)
            if dot_decimal_matches:
                violations.append(
                    ReportViolation(
                        error_class=12,
                        title="Formatação Decimal Fora do Padrão pt-BR",
                        message=f"Número com ponto decimal no lugar de vírgula detectado: {', '.join(dot_decimal_matches[:3])}",
                        section="Forma e Gramática",
                    )
                )

        grammar_matches = re.findall(r"\b1\s+(?:leituras|ciclos|amostras|filtros|quarentenas)\b|\ba\s+volume\b", non_math, flags=re.IGNORECASE)
        if grammar_matches:
            violations.append(
                ReportViolation(
                    error_class=12,
                    title="Erro de Concordância Gramatical",
                    message=f"Erro de concordância identificado no texto: {', '.join(grammar_matches[:3])}.",
                    section="Forma e Gramática",
                )
            )
        return violations
