# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class ReportBlockBase(ABC):
    """
    Abstract base class for modular XAI Markdown report block renderers.
    Follows Single Responsibility (SRP) and Interface Segregation (ISP) principles.
    """

    def __init__(self, templates: Dict[str, Any]) -> None:
        self.templates = templates

    def _t(self, key: str, default: str = "", **kwargs) -> str:
        """Helper to resolve localized string templates."""
        tmpl = self.templates.get(key, default)
        if kwargs and tmpl:
            try:
                return tmpl.format(**kwargs)
            except KeyError:
                class SafeDict(dict):
                    def __missing__(self, k):
                        return f"{{{k}}}"
                return tmpl.format_map(SafeDict(**kwargs))
            except Exception:
                return tmpl
        return tmpl

    @abstractmethod
    def render(self, lines: List[str], block: Dict[str, Any], context: Dict[str, Any]) -> None:
        """
        Renders a specific layout block into the lines buffer.
        :param lines: Target list of strings accumulating Markdown output.
        :param block: Layout configuration block descriptor.
        :param context: Unified execution and analytical data context dictionary.
        """
        pass
