# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Any, Dict, Optional
from src.xai.report_block_base import ReportBlockBase
from src.xai.report_header_cover_renderer import ReportHeaderCoverRenderer
from src.xai.report_executive_summary_renderer import ReportExecutiveSummaryRenderer
from src.xai.report_text_section_renderer import ReportTextSectionRenderer
from src.xai.report_equations_renderer import ReportEquationsRenderer
from src.xai.report_guardian_table_renderer import ReportGuardianTableRenderer
from src.xai.report_consolidated_summary_renderer import ReportConsolidatedSummaryRenderer
from src.xai.report_annex_cards_renderer import ReportAnnexCardsRenderer
from src.xai.report_closing_directives_renderer import ReportClosingDirectivesRenderer


class ReportBlockRegistry:
    """
    Registry for dynamic mapping and instantiation of report block renderers.
    Satisfies Open-Closed Principle (OCP) by allowing new block renderers to be registered
    without modifying existing builder logic.
    """

    def __init__(self) -> None:
        self._renderers: Dict[str, ReportBlockBase] = {}

    def register(self, block_type: str, renderer: ReportBlockBase) -> None:
        """Registers a renderer instance for a specific block type."""
        self._renderers[block_type] = renderer

    def get(self, block_type: str) -> Optional[ReportBlockBase]:
        """Retrieves registered renderer for a given block type."""
        return self._renderers.get(block_type)

    @classmethod
    def create_default(cls, templates: Dict[str, Any]) -> "ReportBlockRegistry":
        """Factory method to instantiate and populate registry with standard SYNAPSE XAI renderers."""
        registry = cls()
        registry.register("header_cover", ReportHeaderCoverRenderer(templates))
        registry.register("executive_summary", ReportExecutiveSummaryRenderer(templates))
        registry.register("section", ReportTextSectionRenderer(templates))
        registry.register("equations_block", ReportEquationsRenderer(templates))
        registry.register("guardian_table", ReportGuardianTableRenderer(templates))
        registry.register("consolidated_summary", ReportConsolidatedSummaryRenderer(templates))
        registry.register("annex_cards", ReportAnnexCardsRenderer(templates))
        closing_renderer = ReportClosingDirectivesRenderer(templates)
        registry.register("closing_directives", closing_renderer)
        registry.register("quesitos_closing", closing_renderer)
        return registry
