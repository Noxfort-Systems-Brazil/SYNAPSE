# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Multi-Station XAI Report Builder.

SOLID Compliance:
- [SRP] Pure high-level orchestrator for modular ABNT report assembly.
- [OCP] Block rendering delegated to pluggable registry and layout JSON configuration.
- [DIP] Context synthesis delegated to specialized domain services.
"""

import logging
from typing import Any, Dict, List, Optional

from src.xai.xai_template_repository import XaiTemplateRepository
from src.xai.report_block_registry import ReportBlockRegistry
from src.xai.report_metrics_transformer import ReportMetricsTransformer
from src.context.station_attribution_builder import StationAttributionBuilder
from src.context.zero_trust_guardian_calculator import ZeroTrustGuardianCalculator
from src.context.corridor_recommendation_builder import CorridorRecommendationBuilder

logger = logging.getLogger("Synapse.XAI.MultiStationReportBuilder")


class MultiStationReportBuilder:
    """
    Pure orchestrator for ABNT NBR 10719 multi-station XAI audit reports.
    Satisfies SRP, OCP, and DIP by delegating context preparation to domain services
    and block rendering to a pluggable registry.
    """

    def __init__(
        self,
        templates: Optional[Dict[str, Any]] = None,
        registry: Optional[ReportBlockRegistry] = None,
        metrics_transformer: Optional[ReportMetricsTransformer] = None,
    ) -> None:
        self._custom_templates = templates is not None
        self.templates = templates if templates is not None else XaiTemplateRepository.get_templates_for_language("pt_br")
        self.registry = registry if registry is not None else ReportBlockRegistry.create_default(self.templates)
        self.metrics_transformer = metrics_transformer if metrics_transformer is not None else ReportMetricsTransformer()

    def _t(self, key: str, default: str = "", **kwargs) -> str:
        tmpl = self.templates.get(key, default)
        if kwargs and tmpl:
            try:
                return tmpl.format(**kwargs)
            except Exception:
                return tmpl
        return tmpl

    def build_markdown(
        self,
        sensors: Optional[List[Dict[str, Any]]] = None,
        safety_interventions: Optional[List[Dict[str, Any]]] = None,
        xai_result: Optional[Dict[str, Any]] = None,
        report_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Orchestrates end-to-end assembly of technical ABNT report Markdown dynamically
        from document_layout configuration blocks for the requested language.
        """
        lines: List[str] = []
        r_data = report_data or {}
        language = r_data.get("language") or "pt_br"
        templates = self.templates if self._custom_templates else XaiTemplateRepository.get_templates_for_language(language)
        registry = self.registry if self._custom_templates else ReportBlockRegistry.create_default(templates)

        active_sensors = sensors if sensors is not None else r_data.get("sensors", [])
        active_safety = safety_interventions if safety_interventions is not None else r_data.get("safetyInterventions", [])

        sensors_lookup = {str(s.get("id", "")): s for s in active_sensors}
        agent_ids = [str(s.get("id", "")) for s in active_sensors] if active_sensors else ["RAD_01", "LACO_01", "CAM_OCR_01", "RAD_02"]

        # 1. Domain Service: Feature attributions & Captum IG charts
        analyses, global_image_base64, _ = StationAttributionBuilder.build_attributions_and_charts(
            agent_ids=agent_ids,
            sensors_lookup=sensors_lookup,
        )

        # 2. Metric normalization
        metrics_by_agent = self.metrics_transformer.transform_agent_metrics(analyses)

        # 3. Domain Service: Zero-Trust safeguards accounting and narratives
        guardian_stats, filtered_safety, totals = ZeroTrustGuardianCalculator.calculate(
            agent_ids=agent_ids,
            sensors_lookup=sensors_lookup,
            active_safety=active_safety,
            analyses=analyses,
        )

        # 4. Domain Service: Corridor classification, recommendations and legal filters
        corridor_data = CorridorRecommendationBuilder.build(
            sensors=active_sensors,
            sensors_lookup=sensors_lookup,
            report_data=r_data,
            templates=templates,
        )

        # 5. Assemble unified execution context
        context: Dict[str, Any] = {
            "agent_ids": agent_ids,
            "sensors_lookup": sensors_lookup,
            "analyses": analyses,
            "global_image_base64": global_image_base64,
            "guardian_stats": guardian_stats,
            "metrics_by_agent": metrics_by_agent,
            "safety_interventions": filtered_safety,
            "templates": templates,
            "language": language,
            "report_data": r_data,
            "protocol": r_data.get("protocol", "RELATORIO-TRAFEGO-2026"),
            "process_number": r_data.get("processNumber", "A vincular (Protocolo SEI)"),
            "city_hall": r_data.get("cityHall") or r_data.get("city_hall", "PREFEITURA DO MUNICÍPIO"),
            "authority_name": r_data.get("authorityName", "(A preencher pelo Responsável Técnico)"),
            "authority_role": r_data.get("authorityRole", "Engenheiro de Tráfego / Responsável Técnico"),
            "registration_number": r_data.get("registrationNumber", "CREA / ART a vincular"),
            **totals,
            **corridor_data,
        }

        # 6. Dispatch layout blocks to pluggable renderers
        layout = templates.get("document_layout", [])
        for block in layout:
            b_type = block.get("type", "")
            renderer = registry.get(b_type)
            if renderer:
                renderer.render(lines, block, context)
            else:
                logger.warning(f"[MultiStationReportBuilder] No registered renderer for block type '{b_type}'")

        full_markdown = "\n".join(lines)
        return {
            "status": "complete",
            "image_base64": global_image_base64,
            "text_content": full_markdown,
            "metrics_by_agent": metrics_by_agent,
        }
