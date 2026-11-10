# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
ABNT NBR 10719 & CTB Section Orchestrator for Microsoft Word (.docx).

SOLID & Clean Architecture:
- [SRP] Single Responsibility: Acts as a pure, lightweight facade/orchestrator coordinating
  specialized section renderers located in the `src.xai` domain module.
- [OCP] Open/Closed Principle: Sections are rendered by decoupled renderer strategies.
- [DIP] Dependency Inversion: Orchestrator delegates formatting logic to domain renderers.
"""

from typing import Dict, Any, Union
from docx import Document

from src.domain.official_report import OfficialReportData
from src.xai import (
    DocxHeaderCoverRenderer,
    DocxExecutiveSummaryRenderer,
    DocxTelemetryGuardianRenderer,
    DocxMathXaiRenderer,
    DocxClosingDirectivesRenderer,
)


class AbntDocxSectionOrchestrator:
    """
    Pure orchestrator coordinating all Microsoft Word (.docx) report sections
    in strict compliance with ABNT NBR 10719:2015 and CTB metrology requirements.
    """

    def __init__(
        self,
        cover_renderer: DocxHeaderCoverRenderer = None,
        exec_renderer: DocxExecutiveSummaryRenderer = None,
        telemetry_renderer: DocxTelemetryGuardianRenderer = None,
        math_renderer: DocxMathXaiRenderer = None,
        closing_renderer: DocxClosingDirectivesRenderer = None,
    ):
        self.cover_renderer = cover_renderer or DocxHeaderCoverRenderer()
        self.exec_renderer = exec_renderer or DocxExecutiveSummaryRenderer()
        self.telemetry_renderer = telemetry_renderer or DocxTelemetryGuardianRenderer()
        self.math_renderer = math_renderer or DocxMathXaiRenderer()
        self.closing_renderer = closing_renderer or DocxClosingDirectivesRenderer()

    def render_all_sections(
        self,
        doc: Document,
        report_data: Union[OfficialReportData, Dict[str, Any]],
        font_family: str,
        base_font_size_pt: float,
        dt_str: str,
        align_mode: Any,
        line_spacing_multiplier: float,
    ) -> None:
        """Executes full sequence of formal municipal report sections."""
        data_dict = report_data.to_dict() if isinstance(report_data, OfficialReportData) else report_data

        self.cover_renderer.render(doc, report_data, font_family, base_font_size_pt, dt_str)
        self.exec_renderer.render(doc, data_dict, font_family, base_font_size_pt, align_mode, line_spacing_multiplier)
        self.telemetry_renderer.render(doc, data_dict, font_family, base_font_size_pt, align_mode, line_spacing_multiplier)
        self.math_renderer.render(doc, data_dict, font_family, base_font_size_pt, align_mode, line_spacing_multiplier)
        self.closing_renderer.render(doc, data_dict, font_family, base_font_size_pt, align_mode, line_spacing_multiplier)


# ==============================================================================
# Backward-Compatible Public Module Functions (Delegating to XAI Renderers)
# ==============================================================================

def render_header_and_cover(
    doc: Document,
    report_data: Union[OfficialReportData, Dict[str, Any]],
    font_family: str,
    base_font_size_pt: float,
    dt_str: str,
) -> None:
    """Renders formal cover and institutional header."""
    DocxHeaderCoverRenderer().render(doc, report_data, font_family, base_font_size_pt, dt_str)


def render_part_1_executive_summary(
    doc: Document,
    report_data: Dict[str, Any],
    font_family: str,
    base_font_size_pt: float,
    align_mode: Any,
    line_spacing_multiplier: float,
) -> None:
    """Renders Part I - Executive Summary with Synthetic Station Audit Table."""
    DocxExecutiveSummaryRenderer().render(doc, report_data, font_family, base_font_size_pt, align_mode, line_spacing_multiplier)


def render_part_2_and_3_diagnosis_and_telemetry(
    doc: Document,
    report_data: Dict[str, Any],
    font_family: str,
    base_font_size_pt: float,
    align_mode: Any,
    line_spacing_multiplier: float,
) -> None:
    """Renders Part II and III - Operational Diagnosis, Corridor Metadata, Sensor Telemetry and Zero-Trust Guardrails."""
    DocxTelemetryGuardianRenderer().render(doc, report_data, font_family, base_font_size_pt, align_mode, line_spacing_multiplier)


def render_part_4_and_5_math_and_xai(
    doc: Document,
    report_data: Dict[str, Any],
    font_family: str,
    base_font_size_pt: float,
    align_mode: Any,
    line_spacing_multiplier: float,
) -> None:
    """Renders Part IV and V - Calculation Memorial and XAI Explainability."""
    DocxMathXaiRenderer().render(doc, report_data, font_family, base_font_size_pt, align_mode, line_spacing_multiplier)


def render_part_6_7_and_8_closing(
    doc: Document,
    report_data: Dict[str, Any],
    font_family: str,
    base_font_size_pt: float,
    align_mode: Any,
    line_spacing_multiplier: float,
) -> None:
    """Renders Part VI, VII and VIII - Technical Findings, Legal Framework, Signatures and References."""
    DocxClosingDirectivesRenderer().render(doc, report_data, font_family, base_font_size_pt, align_mode, line_spacing_multiplier)
