# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Backward compatibility proxy for src.services.report.report_data_collector.
Redirects all symbols to the flat modular package src.report.
"""

from src.report import (
    TrafficReportTemplateLoader,
    TrafficReportDataCollector,
    DEFAULT_TEMPLATE_PATH,
)

__all__ = [
    "TrafficReportTemplateLoader",
    "TrafficReportDataCollector",
    "DEFAULT_TEMPLATE_PATH",
]
