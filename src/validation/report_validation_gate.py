# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Report Validation Gate (ReportValidationGate).

Facade coordinating the 12 canonical error classes and emission criteria for SYNAPSE XAI traffic reports.
Delegates domain policies and specifications to modular rule classes in src.validation.
"""

from typing import Any, Dict, List, Optional

from src.validation.exceptions import ReportValidationError, ReportViolation
from src.validation.pre_markdown_rules import (
    DataPresenceRule,
    WorstCriteriaSeverityRule,
    SourceTypologyPreRule,
    StationNarrativePreRule,
    RecommendationConfidenceRule,
    WeightsConservationRule,
    AvailabilityConciliationRule,
    NormativeApplicabilityRule,
)
from src.validation.textual_style_rules import (
    TemplateLeakRule,
    ProhibitedTermsRule,
    ThresholdsTableRule,
    ParametricInterdependenceRule,
    GrammarAndFormattingRule,
)
from src.validation.analytical_cross_rules import (
    NumericalSpeedRule,
    EquationLintingRule,
    SourceTypologyPostRule,
    Section3WeightsRule,
)
from src.validation.critical_points_gate_rule import CriticalPointsGateRule


class ReportValidationGate:
    """
    Validation Gate Facade that inspects report data structures (pre-markdown)
    and rendered markdown content (post-markdown) before official emission.
    """

    PROHIBITED_TERMS = ProhibitedTermsRule.PROHIBITED_TERMS
    INTERNAL_LEAKS = TemplateLeakRule.INTERNAL_LEAKS
    REQUIRED_EQUATION_TAGS = EquationLintingRule.REQUIRED_EQUATION_TAGS

    PRE_RULES = [
        DataPresenceRule(),
        WorstCriteriaSeverityRule(),
        SourceTypologyPreRule(),
        StationNarrativePreRule(),
        RecommendationConfidenceRule(),
        WeightsConservationRule(),
        AvailabilityConciliationRule(),
        NormativeApplicabilityRule(),
    ]

    POST_RULES = [
        TemplateLeakRule(),
        ProhibitedTermsRule(),
        ThresholdsTableRule(),
        ParametricInterdependenceRule(),
        NumericalSpeedRule(),
        EquationLintingRule(),
        GrammarAndFormattingRule(),
        SourceTypologyPostRule(),
        Section3WeightsRule(),
        CriticalPointsGateRule(),
    ]

    @classmethod
    def validate_pre_markdown(
        cls, report_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> List[ReportViolation]:
        """Validates raw data structures, weights, source typologies, and consistency prior to compiling documents."""
        violations: List[ReportViolation] = []
        for rule in cls.PRE_RULES:
            v_list = rule.validate_pre(report_data, context)
            violations.extend(v_list)
            # If data is completely absent, halt further pre-checks early
            if isinstance(rule, DataPresenceRule) and v_list:
                break
        return violations

    @classmethod
    def validate_post_markdown(
        cls, markdown_text: str, report_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> List[ReportViolation]:
        """Validates rendered Markdown document for textual leaks, prohibited terms, formatting and equations."""
        violations: List[ReportViolation] = []
        for rule in cls.POST_RULES:
            v_list = rule.validate_post(markdown_text, report_data, context)
            violations.extend(v_list)
            # If document is empty, halt further post-checks early
            if isinstance(rule, TemplateLeakRule) and any(v.title == "Documento Vazio" for v in v_list):
                break
        return violations

    @classmethod
    def assert_valid_report(
        cls, report_data: Dict[str, Any], markdown_text: Optional[str] = None, context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Executes pre-markdown and post-markdown validation. Raises ReportValidationError if any violation is found."""
        pre_violations = cls.validate_pre_markdown(report_data, context)
        post_violations = cls.validate_post_markdown(markdown_text, report_data, context) if markdown_text else []

        all_violations = pre_violations + post_violations
        if all_violations:
            raise ReportValidationError(
                f"Document emission halted by ReportValidationGate: {len(all_violations)} violation(s) detected.",
                violations=all_violations,
            )

    # -------------------------------------------------------------------------
    # Backward-Compatible Rule Convenience Methods
    # -------------------------------------------------------------------------
    @classmethod
    def assert_worst_criteria_severity(cls, report_data: Dict[str, Any]) -> List[ReportViolation]:
        return WorstCriteriaSeverityRule.validate_severity(report_data)

    @classmethod
    def assert_vocabulary_matches_source_type(
        cls, report_data: Dict[str, Any], markdown_text: Optional[str] = None, context: Optional[Dict[str, Any]] = None
    ) -> List[ReportViolation]:
        violations = SourceTypologyPreRule.validate_pre_typology(report_data)
        if markdown_text:
            violations.extend(SourceTypologyPostRule.validate_post_typology(markdown_text, report_data, context))
        return violations

    @classmethod
    def assert_section3_matches_annex_cards(
        cls, markdown_text: str, report_data: Dict[str, Any], context: Optional[Dict[str, Any]] = None
    ) -> List[ReportViolation]:
        return Section3WeightsRule.validate_section3(markdown_text)

    @classmethod
    def assert_equation_greek_symbols_match_text(cls, markdown_text: str) -> List[ReportViolation]:
        return EquationLintingRule.validate_equations(markdown_text)

    @classmethod
    def assert_no_label_description_redundancy(cls, markdown_text: str) -> List[ReportViolation]:
        return GrammarAndFormattingRule.validate_redundancy(markdown_text)
