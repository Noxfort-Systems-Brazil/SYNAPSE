# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Any, Dict, List
from src.xai.report_block_base import ReportBlockBase


class ReportTextSectionRenderer(ReportBlockBase):
    """
    Renders pure text sections, institutional intros, and legal guidelines.
    """

    def render(self, lines: List[str], block: Dict[str, Any], context: Dict[str, Any]) -> None:
        agent_ids = context.get("agent_ids", [])
        total_agents = len(agent_ids)

        format_kwargs = dict(context)
        format_kwargs["total_agents"] = total_agents

        title_key = block.get("title_key", "")
        if title_key and self._t(title_key):
            lines.append(self._t(title_key, **format_kwargs))

        for c_key in block.get("content_keys", []):
            text = self._t(c_key, **format_kwargs)
            if text:
                lines.append(text)
                lines.append("")
