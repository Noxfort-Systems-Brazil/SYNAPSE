# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Report Command Handler (SOLID: SRP & DIP).

Encapsulates all IPC actions related to official municipal traffic reports and DOCX export.
Decoupled from generic system lifecycle operations.
"""

import os
from typing import Any, Dict, Optional

from src.ipc.ipc_protocol import IpcMessage
from src.interfaces.reports import ITrafficReportService
from src.services.traffic_report_service import TrafficReportService
from src.factories.jurist_factory import JuristFactory
from src.utils.logging_setup import get_logger

logger = get_logger("Handlers.Report")


class ReportCommandHandler:
    """
    Dedicated IPC handler for Traffic Engineering Reports and ABNT exports.
    """

    def __init__(
        self,
        controller: Optional[Any] = None,
        report_service: Optional[ITrafficReportService] = None,
        audit_logger: Optional[Any] = None,
        jurist_agent: Optional[Any] = None,
    ):
        self.controller = controller
        self.report_service = report_service
        self.audit_logger = audit_logger
        self.jurist_agent = jurist_agent

    def _get_service(self) -> ITrafficReportService:
        """Lazily obtains or instantiates TrafficReportService with Jurist SLM."""
        if self.report_service:
            return self.report_service
        app_state = getattr(self.controller, "app_state", None)
        if self.jurist_agent is None:
            try:
                self.jurist_agent = JuristFactory.create()
            except Exception as e:
                logger.warning(f"Could not instantiate JuristAgent for report handler: {e}")
        return TrafficReportService(app_state=app_state, jurist_agent=self.jurist_agent)

    def _get_current_user(self) -> str:
        sec = getattr(self.controller, "security_manager", None)
        get_user_fn = getattr(sec, "get_current_user", None) if sec else None
        if callable(get_user_fn):
            u = get_user_fn()
            if u:
                return str(u)
        return "OPERATOR_LOCAL"

    def handle_generate_official_report(self, msg: IpcMessage) -> Dict[str, Any]:
        """Synthesizes the complete, authoritative Official Municipal Traffic Audit Report."""
        payload = msg.payload or {}
        result_id = payload.get("result_id")
        municipal_config = payload.get("municipal_config")
        xai_result = payload.get("xai_result")
        typography_options = payload.get("typography_options")
        language = payload.get("language") or "pt_BR"

        service = self._get_service()
        report_output = service.build_report(
            result_id=result_id,
            municipal_config=municipal_config,
            xai_result=xai_result,
            typography_options=typography_options,
            language=language,
        )

        if not report_output.get("ready", True):
            return {
                "success": False,
                "ready": False,
                "status": report_output.get("status", "DATA_GENERATING"),
                "message": report_output.get(
                    "message",
                    "Os dados de telemetria e fusão neural estão sendo gerados na malha viária."
                ),
            }

        if self.audit_logger:
            protocol = report_output.get("report", {}).get("protocol", "DESCONHECIDO")
            self.audit_logger.log_action(
                self._get_current_user(),
                "GENERATE_OFFICIAL_REPORT",
                f"Emissão de Relatório Técnico Explicativo de Tráfego: {protocol}",
            )

        return {
            "success": True,
            "ready": True,
            "report": report_output["report"],
            "formatted_markdown": report_output["formatted_markdown"],
            "preview_html": report_output.get("preview_html", ""),
        }

    def handle_export_official_report_docx(self, msg: IpcMessage) -> Dict[str, Any]:
        """Exports the official traffic report to Microsoft Word (.docx) native format."""
        payload = msg.payload or {}
        report_data = payload.get("report")
        output_path = payload.get("output_path")
        typography_options = payload.get("typography_options")
        language = payload.get("language") or "pt_BR"

        service = self._get_service()

        if not report_data:
            report_output = service.build_report(
                result_id=payload.get("result_id"),
                municipal_config=payload.get("municipal_config"),
                xai_result=payload.get("xai_result"),
                typography_options=typography_options,
                language=language,
            )
            if not report_output.get("ready", True):
                return {
                    "success": False,
                    "ready": False,
                    "error": report_output.get(
                        "message",
                        "Não é possível exportar laudo técnico: dados de telemetria em processamento."
                    ),
                }
            report_data = report_output["report"]

        if isinstance(report_data, dict):
            report_data.setdefault("language", language)

        if not isinstance(report_data, dict) or not report_data:
            return {
                "success": False,
                "ready": False,
                "error": "Dados do laudo pericial inválidos ou em processamento.",
            }

        protocol = report_data.get("protocol", "RELATORIO-TRAFEGO")
        if not output_path:
            downloads_dir = os.path.expanduser("~/Downloads")
            os.makedirs(downloads_dir, exist_ok=True)
            output_path = os.path.join(downloads_dir, f"Laudo_Tecnico_Trafego_{protocol}.docx")
        else:
            output_path = os.path.abspath(os.path.expanduser(output_path))
            if os.path.isdir(output_path):
                output_path = os.path.join(output_path, f"Laudo_Tecnico_Trafego_{protocol}.docx")
            elif not output_path.lower().endswith(".docx"):
                output_path = f"{output_path}.docx"

        saved_file = service.export_docx(
            report_data=report_data,
            output_path=output_path,
            typography_options=typography_options,
        )

        if self.audit_logger:
            self.audit_logger.log_action(
                self._get_current_user(),
                "EXPORT_OFFICIAL_REPORT_DOCX",
                f"Exportação de Laudo Técnico para DOCX: {protocol} -> {saved_file}",
            )

        return {
            "success": True,
            "output_path": saved_file,
            "protocol": protocol,
        }
