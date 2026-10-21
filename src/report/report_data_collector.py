# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Report Data Collector (Facade Pattern).

Provides a unified, backward-compatible facade delegating specialized tasks to
modular single-responsibility components under src/report/.
"""

from typing import Dict, Any, List, Optional

from src.report.traffic_kinematics import TrafficKinematicsCalculator
from src.report.sensor_extractor import SensorTelemetryExtractor
from src.report.network_summary import NetworkSummaryCalculator
from src.report.attribution_extractor import XAIAttributionExtractor
from src.report.jurist_diagnosis import JuristDiagnosisGenerator
from src.report.template_loader import (
    TrafficReportTemplateLoader,
    MunicipalConfigResolver,
    DEFAULT_TEMPLATE_PATH,
)


class TrafficReportDataCollector:
    """
    Facade aggregating telemetry, attributions, kinematics and diagnostics.
    Delegates all domain operations to specialized single-responsibility classes.
    """

    @staticmethod
    def _derive_sensor_kinematics(speed_val: float, raw_source: Any = None) -> Dict[str, str]:
        """Delegates kinematic derivation to TrafficKinematicsCalculator."""
        return TrafficKinematicsCalculator.derive_sensor_kinematics(speed_val, raw_source)

    @staticmethod
    def extract_sensors(app_state: Any) -> List[Dict[str, Any]]:
        """Delegates sensor extraction to SensorTelemetryExtractor."""
        return SensorTelemetryExtractor.extract_sensors(app_state)

    @staticmethod
    def resolve_municipal_config(
        cfg: Optional[Dict[str, Any]],
        template: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Delegates municipal config resolution to MunicipalConfigResolver."""
        return MunicipalConfigResolver.resolve_municipal_config(cfg, template)

    @staticmethod
    def compute_network_summary(sensors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Delegates network aggregation to NetworkSummaryCalculator."""
        return NetworkSummaryCalculator.compute_network_summary(sensors)

    @staticmethod
    def extract_attributions(
        xai_result: Optional[Dict[str, Any]],
        sensors: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Delegates XAI attribution extraction to XAIAttributionExtractor."""
        return XAIAttributionExtractor.extract_attributions(xai_result, sensors)

    @staticmethod
    def generate_jurist_diagnosis(
        jurist_agent: Optional[Any],
        sensors: List[Dict[str, Any]],
        summary: Dict[str, Any],
        regime: str,
        comparative: Dict[str, Any],
        xai_result: Optional[Dict[str, Any]],
    ) -> str:
        """Delegates jurist diagnosis generation to JuristDiagnosisGenerator."""
        return JuristDiagnosisGenerator.generate_jurist_diagnosis(
            jurist_agent, sensors, summary, regime, comparative, xai_result
        )


__all__ = [
    "TrafficReportDataCollector",
    "TrafficReportTemplateLoader",
    "DEFAULT_TEMPLATE_PATH",
]
