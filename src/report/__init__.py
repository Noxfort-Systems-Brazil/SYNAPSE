# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Report Package (Flat Architecture under src/report).

Modular domain components for traffic engineering reports:
- TrafficKinematicsCalculator: Macroscopic traffic flow physics (Greenshields / LWR).
- SensorTelemetryExtractor: Live sensor telemetry extraction and normalization.
- NetworkSummaryCalculator: Macroscopic corridor aggregation and HCM level of service.
- XAIAttributionExtractor: Explainability attribution and kinematic sensitivity.
- JuristDiagnosisGenerator: JuristAgent SLM inference and analytical synthesis.
- TrafficReportTemplateLoader & MunicipalConfigResolver: Normative template I/O and config resolution.
- TrafficReportDataCollector: Cohesive Facade providing unified access.
"""

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
from src.report.report_data_collector import TrafficReportDataCollector

__all__ = [
    "TrafficKinematicsCalculator",
    "SensorTelemetryExtractor",
    "NetworkSummaryCalculator",
    "XAIAttributionExtractor",
    "JuristDiagnosisGenerator",
    "TrafficReportTemplateLoader",
    "MunicipalConfigResolver",
    "TrafficReportDataCollector",
    "DEFAULT_TEMPLATE_PATH",
]
