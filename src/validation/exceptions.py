# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Report Validation Exceptions.

Defines rich exception types raised by ReportValidationGate when any of the
12 report error classes are detected prior to or during document generation.
"""

from typing import Any, Dict, List, Optional


class ReportViolation:
    """Represents a discrete rule violation detected during report auditing."""

    def __init__(
        self,
        error_class: int,
        title: str,
        message: str,
        section: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.error_class = error_class
        self.title = title
        self.message = message
        self.section = section or "General"
        self.context = context or {}

    @property
    def code(self) -> str:
        return self.title.upper().replace(" ", "_")

    def __repr__(self) -> str:
        return f"[Class {self.error_class:02d} - {self.title}] ({self.section}): {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_class": self.error_class,
            "title": self.title,
            "message": self.message,
            "section": self.section,
            "context": self.context,
        }


class ReportValidationError(ValueError):
    """
    Raised by ReportValidationGate when report data or generated markdown
    fails one or more of the 12 canonical emission criteria.
    """

    def __init__(self, message: str, violations: Optional[List[ReportViolation]] = None) -> None:
        super().__init__(message)
        self.violations: List[ReportViolation] = violations or []

    @property
    def violation_summary(self) -> str:
        if not self.violations:
            return str(self)
        lines = [f"ReportValidationError: {len(self.violations)} violation(s) blocked document emission:"]
        for v in self.violations:
            lines.append(f"  - [Class {v.error_class:02d}] {v.title} ({v.section}): {v.message}")
        return "\n".join(lines)
