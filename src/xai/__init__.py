# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from src.xai.xai_template_repository import XaiTemplateRepository
from src.xai.chart_renderer import ChartRenderer
from src.xai.report_metrics_transformer import ReportMetricsTransformer
from src.xai.report_block_base import ReportBlockBase
from src.xai.report_header_cover_renderer import ReportHeaderCoverRenderer
from src.xai.report_closing_directives_renderer import ReportClosingDirectivesRenderer
from src.xai.report_block_registry import ReportBlockRegistry
from src.xai.multi_station_report_builder import MultiStationReportBuilder
from src.xai.docx_header_cover_renderer import DocxHeaderCoverRenderer
from src.xai.docx_executive_summary_renderer import DocxExecutiveSummaryRenderer
from src.xai.docx_telemetry_guardian_renderer import DocxTelemetryGuardianRenderer
from src.xai.docx_math_xai_renderer import DocxMathXaiRenderer
from src.xai.docx_closing_directives_renderer import DocxClosingDirectivesRenderer

__all__ = [
    "XaiTemplateRepository",
    "ChartRenderer",
    "ReportMetricsTransformer",
    "ReportBlockBase",
    "ReportHeaderCoverRenderer",
    "ReportClosingDirectivesRenderer",
    "ReportBlockRegistry",
    "MultiStationReportBuilder",
    "DocxHeaderCoverRenderer",
    "DocxExecutiveSummaryRenderer",
    "DocxTelemetryGuardianRenderer",
    "DocxMathXaiRenderer",
    "DocxClosingDirectivesRenderer",
]
