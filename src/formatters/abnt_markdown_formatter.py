# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
ABNT NBR 10719 & NBR 14724 Standardized Markdown Report Formatter.

SOLID Compliance:
- [SRP] Single Responsibility: Exclusively converts OfficialReportData into ABNT-compliant Markdown.
- [OCP] Open for extension via IReportFormatter and MultiStationReportBuilder.
- [LSP] Full compliance with IReportFormatter protocol.
Focuses strictly on Neural Sensor Fusion & Metrological Perception Auditing.
"""

from datetime import datetime
from typing import Dict, Any, Optional

from src.interfaces.reports import IReportFormatter
from src.xai.multi_station_report_builder import MultiStationReportBuilder
from src.formatters.report_post_processor import ReportPostProcessor
from src.utils.logging_setup import get_logger

logger = get_logger("Formatters.AbntMarkdownReportFormatter")


class AbntMarkdownReportFormatter(IReportFormatter):
    """
    Renders official traffic engineering reports in strict compliance with ABNT NBR 10719:2015.
    Delegates modular assembly to MultiStationReportBuilder.
    """

    def __init__(self, builder: Optional[MultiStationReportBuilder] = None) -> None:
        self.builder = builder or MultiStationReportBuilder()

    def format(self, report_data: Dict[str, Any]) -> str:
        """Renders complete multi-part ABNT NBR 10719 pericial text representation."""
        try:
            sensors = report_data.get("sensors", [])
            interventions = report_data.get("safetyInterventions", [])
            xai_result = report_data.get("xaiResult")

            result = self.builder.build_markdown(
                sensors=sensors,
                safety_interventions=interventions,
                xai_result=xai_result,
                report_data=report_data,
            )
            raw_markdown = result.get("text_content", "")
            cleaned = ReportPostProcessor.enforce_semantic_consistency(raw_markdown)
            ReportPostProcessor.assert_no_unrendered_placeholders(cleaned)

            # Rule Gate: Enforce all 12 pre-emission validation criteria
            from src.validation.report_validation_gate import ReportValidationGate
            ReportValidationGate.assert_valid_report(report_data=report_data, markdown_text=cleaned)

            return cleaned
        except Exception as e:
            logger.error(f"[AbntMarkdownReportFormatter] Error formatting report via builder: {e}", exc_info=True)
            raise

    def _legacy_format_fallback(self, report_data: Dict[str, Any]) -> str:
        """Fallback formatter ensuring zero-crash resilience in edge environments."""
        r = report_data
        timestamp_raw = r.get("timestamp", datetime.now().isoformat())
        try:
            dt_str = datetime.fromisoformat(timestamp_raw).strftime("%d/%m/%Y às %H:%M:%S")
        except Exception:
            dt_str = str(timestamp_raw)

        sensors = r.get("sensors", [])
        sensors_md = "\n\n".join(
            f"[Dispositivo {i+1}] {s.get('id', '')}\n"
            f"  - Localização / Interseção: {s.get('junction', '')}\n"
            f"  - Tecnologia do Detector: {s.get('equipmentType', '')}\n"
            f"  - Grandezas Medidas: Velocidade={s.get('measuredSpeed', '')} | Fluxo={s.get('measuredFlow', '')} | Ocupação={s.get('occupancyRate', '')}\n"
            f"  - Grau de Saturação: {s.get('saturationDegree', '')}\n"
            f"  - Metrologia Legal: {s.get('inmetroReport', '')}\n"
            f"  - Status Operacional: {s.get('operationalStatus', '')}"
            for i, s in enumerate(sensors)
        )

        net = r.get("networkSummary", {})
        return f"""# LAUDO TÉCNICO PERICIAL DE AUDITORIA METROLÓGICA E FUSÃO NEURAL
**Processo:** {r.get('processNumber', '')} | **Protocolo:** {r.get('protocol', '')}
**Data:** {dt_str}

## PARTE I — SUMÁRIO EXECUTIVO
- Corredores: {net.get('corridorsMonitored', '')}
- Volume Total: {net.get('totalHourlyFlow', '')}
- Velocidade Média: {net.get('networkMeanSpeed', '')}

## PARTE II — AUDITORIA DE DETECTORES
{sensors_md}
"""
