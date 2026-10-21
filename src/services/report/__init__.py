# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Backward compatibility proxy for src.services.report.
Redirects all symbols to the flat modular package src.report.
"""

from src.report import (
    TrafficKinematicsCalculator,
    SensorTelemetryExtractor,
    NetworkSummaryCalculator,
    XAIAttributionExtractor,
    JuristDiagnosisGenerator,
    TrafficReportTemplateLoader,
    MunicipalConfigResolver,
    TrafficReportDataCollector,
    DEFAULT_TEMPLATE_PATH,
)

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
