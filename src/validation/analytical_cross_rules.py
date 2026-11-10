# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Analytical and Cross-Section Post-Markdown Validation Rules.
Validates numerical consistency, equation linting, section 3 weights, and typology terms.
"""

import re
from typing import Any, Dict, List, Optional
from src.validation.exceptions import ReportViolation
from src.validation.base_rule import PostMarkdownRule


class NumericalSpeedRule(PostMarkdownRule):
    """Rule 8: Cross-section numerical conciliation between executive summary and sensor cards."""

    def validate_post(self, markdown_text: str, report_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[ReportViolation]:
        violations: List[ReportViolation] = []
        sensors = report_data.get("sensors", [])
        if sensors:
            speeds = []
            for s in sensors:
                try:
                    spd = float(str(s.get("measuredSpeed", "")).split()[0].replace(",", "."))
                    speeds.append(spd)
                except Exception:
                    pass
            if speeds:
                calc_avg_spd = sum(speeds) / len(speeds)
                exec_spd_match = re.search(r"(?:velocidade média|average corridor speed|velocidad promedio).*?\*\*([0-9]+[,\.][0-9]+)\s*km/h\*\*", markdown_text, flags=re.IGNORECASE)
                if exec_spd_match:
                    doc_spd = float(exec_spd_match.group(1).replace(",", "."))
                    if abs(doc_spd - calc_avg_spd) > 0.25:
                        violations.append(
                            ReportViolation(
                                error_class=8,
                                title="Divergência Numérica de Velocidade",
                                message=f"Velocidade média no Resumo ({doc_spd:.1f} km/h) diverge da média calculada das fichas ({calc_avg_spd:.1f} km/h).",
                                section="Resumo Executivo (1.2)",
                            )
                        )
        return violations


class EquationLintingRule(PostMarkdownRule):
    """Rule 9: Equation linting, Greek symbol matching, and syntax consistency."""

    REQUIRED_EQUATION_TAGS = ["2.2.1", "2.2.2", "2.2.3", "2.2.4", "2.2.5"]

    @classmethod
    def validate_equations(cls, markdown_text: str) -> List[ReportViolation]:
        from src.validation.equation_consistency_rule import EquationConsistencyRule
        return EquationConsistencyRule().validate_post(markdown_text=markdown_text, report_data={})

    def validate_post(self, markdown_text: str, report_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[ReportViolation]:
        from src.validation.equation_consistency_rule import EquationConsistencyRule
        return EquationConsistencyRule().validate_post(markdown_text=markdown_text, report_data=report_data, context=context)


class SourceTypologyPostRule(PostMarkdownRule):
    """Rule 4: Asserts vocabulary and safety intervention consistency in rendered text."""

    @classmethod
    def validate_post_typology(
        cls, markdown_text: str, report_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> List[ReportViolation]:
        violations: List[ReportViolation] = []
        sensors = report_data.get("sensors", [])
        all_are_feeds = bool(sensors) and all(
            s.get("canonical_source_type") == "third_party_feed"
            or (
                s.get("canonical_source_type") is None
                and any(t in str(s.get("equipmentType", "")).lower() for t in ["feed de terceiros", "waze", "tomtom", "crowdsourcing"])
            )
            for s in sensors
        )

        if all_are_feeds:
            non_math = re.sub(r"\$\$.*?\$\$", "", markdown_text, flags=re.DOTALL)
            non_math = re.sub(r"\$[^\$]+?\$", "", non_math)
            feed_forbidden = [
                (r"\bvelocidade\s+aferida\b", "velocidade aferida"),
                (r"\bradar\s+f[íi]sico\b", "radar físico"),
                (r"\bla[çc]os?(\s+indutivos?)?\b", "laço"),
                (r"\bdetector\s+de\s+campo\b", "detector de campo"),
            ]
            for pat, name in feed_forbidden:
                matches = re.findall(pat, non_math, flags=re.IGNORECASE)
                if matches:
                    violations.append(
                        ReportViolation(
                            error_class=4,
                            title="Vocabulário Incompatível em Relatório de Feeds",
                            message=f"Relatório baseado exclusivamente em feeds de terceiros contém menção indevida a '{name}'.",
                            section="Corpo do Relatório",
                        )
                    )

        interventions = (context or {}).get("safety_interventions", [])
        for it in interventions:
            if isinstance(it, dict):
                eq_id = it.get("equipmentId", "")
                target_sensor = next((s for s in sensors if s.get("id") == eq_id), None)
                if target_sensor and (
                    target_sensor.get("canonical_source_type") == "third_party_feed"
                    or any(t in str(target_sensor.get("equipmentType", "")).lower() for t in ["feed", "api", "waze", "tomtom"])
                ):
                    desc = (str(it.get("irregularityDetected", "")) + " " + str(it.get("correctiveGuardrail", ""))).lower()
                    for term in ["radar", "câmera", "camera", "laço", "ótico", "óptica", "doppler"]:
                        if term in desc:
                            violations.append(
                                ReportViolation(
                                    error_class=4,
                                    title="Intervenção Física Atribuída a Feed",
                                    message=f"Intervenção de segurança para a estação feed '{eq_id}' cita incidente físico ('{term}').",
                                    section="Salvaguardas Operacionais (4)",
                                )
                            )
        return violations

    def validate_post(self, markdown_text: str, report_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[ReportViolation]:
        return self.validate_post_typology(markdown_text, report_data, context)


class Section3WeightsRule(PostMarkdownRule):
    """Rule 7: Validates that Section 3 table row weights sum to 100.0% +/- 0.3%."""

    @classmethod
    def validate_section3(cls, markdown_text: str) -> List[ReportViolation]:
        violations: List[ReportViolation] = []
        sec3_match = re.search(r"(?:## 3\.|### 2\.2).*?(?=(?:## 4\.|### 2\.3|## PARTE III|$))", markdown_text, flags=re.DOTALL)
        if not sec3_match:
            return violations

        sec3_text = sec3_match.group(0)
        table_rows = [line.strip() for line in sec3_text.splitlines() if line.strip().startswith("|") and not line.strip().startswith("| :---")]
        data_rows = [r for r in table_rows if not ("Estação /" in r or "Fatores de Maior Peso" in r or "Variáveis Analisadas" in r)]

        for row in data_rows:
            cols = [c.strip() for c in row.split("|")[1:-1]]
            if len(cols) >= 2:
                weights_col = cols[1]
                pct_matches = re.findall(r"(\d+[,\.]\d+)\s*%", weights_col)
                if pct_matches:
                    total_pct = sum(float(p.replace(",", ".")) for p in pct_matches)
                    if abs(total_pct - 100.0) > 0.3:
                        violations.append(
                            ReportViolation(
                                error_class=7,
                                title="Soma dos Pesos da Seção 3 Incompleta",
                                message=(
                                    f"A linha da Seção 3 ('{cols[0]}') totaliza {total_pct:.1f}% "
                                    f"(esperado: 100,0% ± 0,1%). O Grau de Saturação ou outra variável foi omitida."
                                ),
                                section="Seção 3 (Explicabilidade)",
                            )
                        )
        return violations

    def validate_post(self, markdown_text: str, report_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> List[ReportViolation]:
        return self.validate_section3(markdown_text)
