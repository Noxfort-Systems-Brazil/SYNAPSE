# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Package init for report validation domain specifications and execution gate.
"""

from src.validation.exceptions import (
    ReportValidationError,
    ReportViolation,
)
from src.validation.base_rule import (
    IValidationRule,
    PreMarkdownRule,
    PostMarkdownRule,
)
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
from src.validation.report_validation_gate import ReportValidationGate

__all__ = [
    "ReportValidationError",
    "ReportViolation",
    "IValidationRule",
    "PreMarkdownRule",
    "PostMarkdownRule",
    "DataPresenceRule",
    "WorstCriteriaSeverityRule",
    "SourceTypologyPreRule",
    "StationNarrativePreRule",
    "RecommendationConfidenceRule",
    "WeightsConservationRule",
    "AvailabilityConciliationRule",
    "NormativeApplicabilityRule",
    "TemplateLeakRule",
    "ProhibitedTermsRule",
    "ThresholdsTableRule",
    "ParametricInterdependenceRule",
    "NumericalSpeedRule",
    "EquationLintingRule",
    "GrammarAndFormattingRule",
    "SourceTypologyPostRule",
    "Section3WeightsRule",
    "ReportValidationGate",
]
