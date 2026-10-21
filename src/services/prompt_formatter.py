# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Dict, List, Optional, Any
from src.interfaces.prompts import IPromptBuilder


class _SafeFormatter(dict):
    """Dictionary formatter that preserves missing format keys instead of raising KeyError."""
    def __missing__(self, key: str) -> str:
        return f"{{{key}}}"


class ChatPromptBuilder(IPromptBuilder):
    """
    Service for formatting prompt templates into chat messages for LLM inference.
    
    Responsibilities (SRP):
    - Interpolate dynamic variables into prompt templates safely.
    - Preserve missing variables to prevent formatting crashes.
    - Format system/user roles into standard chat message payloads.
    """

    def build_messages(
        self,
        template: Dict[str, str],
        source: Optional[str] = None,
        status: Optional[str] = None,
        values: Optional[Any] = None,
        **kwargs: Any
    ) -> List[Dict[str, str]]:
        """
        Builds and formats chat messages for an LLM agent from a raw template dictionary.
        
        Args:
            template: Dict containing template keys (e.g. 'system', 'user').
            source: Legacy source identifier.
            status: Legacy state / anomaly status.
            values: Legacy data payload.
            **kwargs: Dynamic contextual variables.
            
        Returns:
            List of message dicts [{'role': 'system', 'content': ...}, {'role': 'user', 'content': ...}].
        """
        context: Dict[str, Any] = dict(kwargs)
        if source is not None:
            context["source"] = source
        if status is not None:
            context["status"] = status
        if values is not None:
            context["values"] = values

        formatter = _SafeFormatter(context)
        system_raw = template.get("system", "")
        user_raw = template.get("user", "")

        system_content = system_raw.format_map(formatter) if system_raw else ""
        user_content = user_raw.format_map(formatter) if user_raw else ""

        messages: List[Dict[str, str]] = []
        if system_content:
            messages.append({"role": "system", "content": system_content})
        if user_content:
            messages.append({"role": "user", "content": user_content})

        return messages
