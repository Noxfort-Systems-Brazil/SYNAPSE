# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: src/services/traffic_report_service.py
# Description: Pure Orchestrator for Official Traffic Audit Reports (SOLID / Clean Architecture).

import random
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from src.interfaces.reports import ITrafficReportService, IReportFormatter
from src.formatters.abnt_markdown_formatter import AbntMarkdownReportFormatter
from src.formatters.abnt_docx_exporter import AbntDocxExporter
from src.formatters.abnt_html_preview_exporter import AbntHtmlPreviewExporter
from src.storage.traffic_snapshot_store import TrafficSnapshotStore
from src.utils.logging_setup import get_logger

# Delegated Data Collectors (SOLID / Flat Architecture)
from src.report import (
    TrafficReportTemplateLoader,
    TrafficReportDataCollector,
    DEFAULT_TEMPLATE_PATH,
)

logger = get_logger("Services.TrafficReport")


class TrafficReportService(ITrafficReportService):
    """
    Pure Orchestrator for Official Municipal Traffic Reports.

    Coordinates:
    - Lock Guard validation (is_data_ready)
    - Normative template resolution (TrafficReportTemplateLoader)
    - Live sensor and telemetry aggregation (TrafficReportDataCollector)
    - Comparative historical snapshot computation (TrafficSnapshotStore)
    - SLM Jurist diagnosis execution
    - Multi-format compilation (Markdown, HTML preview, DOCX)
    """

    def __init__(
        self,
        app_state: Optional[Any] = None,
        xai_manager: Optional[Any] = None,
        jurist_agent: Optional[Any] = None,
        formatter: Optional[IReportFormatter] = None,
        docx_exporter: Optional[AbntDocxExporter] = None,
        preview_exporter: Optional[AbntHtmlPreviewExporter] = None,
        template_path: Optional[str] = None,
        snapshot_store: Optional[Any] = None,
    ):
        self.app_state = app_state
        self.xai_manager = xai_manager
        self.jurist_agent = jurist_agent
        self.formatter: IReportFormatter = formatter or AbntMarkdownReportFormatter()
        self.docx_exporter = docx_exporter or AbntDocxExporter()
        self.preview_exporter = preview_exporter or AbntHtmlPreviewExporter()
        self.template_loader = TrafficReportTemplateLoader(template_path or DEFAULT_TEMPLATE_PATH)
        self.snapshot_store = snapshot_store or TrafficSnapshotStore()

    @property
    def template_path(self) -> str:
        return self.template_loader.template_path

    def _load_template(self) -> Dict[str, Any]:
        return self.template_loader.load_template()

    def _extract_sensors(self) -> List[Dict[str, Any]]:
        return TrafficReportDataCollector.extract_sensors(self.app_state)

    def is_data_ready(self, xai_result: Optional[Dict[str, Any]] = None) -> Tuple[bool, str, str]:
        """Compliance Lock Guard: Asserts whether live sensor telemetry exists."""
        sensors = self._extract_sensors()
        if not sensors:
            return (
                False,
                "DATA_GENERATING",
                "Os dados de telemetria e fusão neural estão sendo gerados na malha viária. "
                "Nenhum detector com telemetria ativa foi identificado no momento."
            )
        return (True, "READY", "Dados prontos para emissão de laudo pericial oficial.")

    def build_report(
        self,
        result_id: Optional[str] = None,
        municipal_config: Optional[Dict[str, Any]] = None,
        xai_result: Optional[Dict[str, Any]] = None,
        typography_options: Optional[Dict[str, Any]] = None,
        override_sensors: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Synthesizes OfficialReportData, Markdown, and A4 HTML preview."""
        sensors = override_sensors if override_sensors is not None else self._extract_sensors()
        if not sensors:
            _, status, msg = self.is_data_ready(xai_result)
            return {
                "ready": False,
                "status": status,
                "message": msg,
                "report": None,
                "formatted_markdown": f"# LAUDO OFICIAL EM PROCESSAMENTO\n\n{msg}",
                "preview_html": None,
            }

        template = self._load_template()
        municipal = TrafficReportDataCollector.resolve_municipal_config(municipal_config, template)
        random_seq = random.randint(1000, 9999)
        protocol = f"RELATORIO-TRAFEGO-2026-{random_seq}"
        process_number = f"{municipal['processPrefix']}0{random_seq}"
        timestamp_str = datetime.now().isoformat()

        network_summary = TrafficReportDataCollector.compute_network_summary(sensors)
        attributions = TrafficReportDataCollector.extract_attributions(xai_result, sensors)
        speeds = [float(str(s.get("measuredSpeed", "")).split()[0].replace(",", ".")) for s in sensors if s.get("measuredSpeed")]
        mean_spd = sum(speeds) / len(speeds) if speeds else 18.4
        flow_regime = "Regime Forçado" if mean_spd < 15.0 else "Regime Estável de Fluxo"

        prev_snap = self.snapshot_store.load_previous_snapshot()
        comparative = self.snapshot_store.compute_comparison(sensors, network_summary, flow_regime, prev_snap)
        self.snapshot_store.save_current_snapshot(
            self.snapshot_store.build_snapshot_payload(protocol, sensors, network_summary, flow_regime)
        )
        observed_diagnosis = TrafficReportDataCollector.generate_jurist_diagnosis(
            self.jurist_agent, sensors, network_summary, flow_regime, comparative, xai_result
        )

        report_data = {
            "protocol": protocol,
            "processNumber": process_number,
            "registrationNumber": municipal["registrationNumber"],
            "authorityName": municipal["authorityName"],
            "authorityRole": municipal["authorityRole"],
            "cityHall": municipal["cityHall"],
            "department": municipal["department"],
            "system": template.get("systemVersion", "SYNAPSE v2.0 Enterprise"),
            "timestamp": timestamp_str,
            "location": template.get("location", {}),
            "networkSummary": network_summary,
            "auditObjective": template.get("auditObjective", ""),
            "observedTrafficDiagnosis": observed_diagnosis,
            "comparativeEvolution": comparative,
            "adaptiveActionExecuted": "Fusão neural multi-sensorial por iTransformer + GATv2 com filtragem PI-DVAE-TCN via HFT-Link gRPC.",
            "sensors": sensors,
            "safetyInterventions": template.get("safetyInterventions", []),
            "attributions": attributions,
            "counterfactualAnalysis": template.get("counterfactualAnalysis", ""),
            "quesitos": template.get("quesitos", []),
            "legalFraming": template.get("legalFraming", []),
            "references": template.get("references", []),
            "operationalSupervision": template.get("operationalSupervision", ""),
            "digitalCertification": template.get("digitalCertification", ""),
        }

        formatted_markdown = self.formatter.format(report_data)
        preview_html = self.preview_exporter.generate_html(report_data, typography_options)

        return {
            "ready": True,
            "status": "READY",
            "report": report_data,
            "formatted_markdown": formatted_markdown,
            "preview_html": preview_html,
        }

    def export_docx(self, report_data: Dict[str, Any], output_path: str, typography_options: Optional[Dict[str, Any]] = None) -> str:
        return self.docx_exporter.export_to_file(report_data, output_path, typography_options)

    def export_docx_bytes(self, report_data: Dict[str, Any], typography_options: Optional[Dict[str, Any]] = None) -> bytes:
        return self.docx_exporter.export_to_bytes(report_data, typography_options)
