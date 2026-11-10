# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Base interfaces and classes for Report Validation Rules (DDD / SOLID Specification).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from src.validation.exceptions import ReportViolation


class IValidationRule(ABC):
    """Domain specification interface for report validation rules."""

    @abstractmethod
    def validate(
        self,
        report_data: Dict[str, Any],
        markdown_text: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[ReportViolation]:
        """Executes the validation rule and returns a list of violations."""
        pass


class PreMarkdownRule(IValidationRule):
    """Abstract base class for data-structure validation prior to markdown rendering."""

    def validate(
        self,
        report_data: Dict[str, Any],
        markdown_text: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[ReportViolation]:
        return self.validate_pre(report_data, context)

    @abstractmethod
    def validate_pre(
        self,
        report_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[ReportViolation]:
        pass


class PostMarkdownRule(IValidationRule):
    """Abstract base class for rendered markdown text inspection."""

    def validate(
        self,
        report_data: Dict[str, Any],
        markdown_text: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[ReportViolation]:
        if markdown_text is None:
            return []
        return self.validate_post(markdown_text, report_data, context)

    @abstractmethod
    def validate_post(
        self,
        markdown_text: str,
        report_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> List[ReportViolation]:
        pass
