# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Domain Contracts & Protocols for Traffic Engineering Reports (SOLID: DIP & ISP).
"""

from typing import Dict, Any, Optional, Protocol, runtime_checkable


@runtime_checkable
class IReportFormatter(Protocol):
    """
    Contract for serializing and formatting official report domain data into target representation.
    """

    def format(self, report_data: Dict[str, Any]) -> str:
        """Transforms structured report data dictionary into formatted textual representation."""
        ...


@runtime_checkable
class ITrafficReportService(Protocol):
    """
    Contract for synthesizing and orchestrating official municipal traffic reports.
    """

    def build_report(
        self,
        result_id: Optional[str] = None,
        municipal_config: Optional[Dict[str, Any]] = None,
        xai_result: Optional[Dict[str, Any]] = None,
        typography_options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Synthesizes structured report data and delegates to injected formatter."""
        ...

    def export_docx(
        self,
        report_data: Dict[str, Any],
        output_path: str,
        typography_options: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Exports report to native Microsoft Word (.docx) file."""
        ...
