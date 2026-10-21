# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Dict, List, Optional, Any, Callable, Protocol, runtime_checkable


@runtime_checkable
class ITemplateLoader(Protocol):
    """Contract for discovering, resolving, loading, caching, and registering prompt templates."""

    def register_language(self, alias: str, canonical_code: str) -> None:
        """Extends supported languages at runtime."""
        ...

    def register_template(self, template_name: str, language: str, template: Dict[str, str]) -> None:
        """Registers an in-memory template."""
        ...

    def register_fallback(self, template_name: str, fallback_template: Dict[str, str]) -> None:
        """Registers a domain-specific fallback template."""
        ...

    def clear_cache(self) -> None:
        """Clears all in-memory cached templates."""
        ...

    def resolve_language(self, language: str) -> str:
        """Maps language aliases to canonical template keys."""
        ...

    def load_template(
        self,
        template_name: str = "jurist",
        language: str = "pt_BR",
        custom_dir: Optional[str] = None
    ) -> Dict[str, str]:
        """Loads and returns template dictionary containing system and user prompts."""
        ...


@runtime_checkable
class IPromptBuilder(Protocol):
    """Contract for formatting dynamic prompt context into LLM chat messages."""

    def build_messages(
        self,
        template: Dict[str, str],
        source: Optional[str] = None,
        status: Optional[str] = None,
        values: Optional[Any] = None,
        **kwargs: Any
    ) -> List[Dict[str, str]]:
        """Interpolates variables into template strings and constructs chat message list."""
        ...


@runtime_checkable
class IResponseSanitizer(Protocol):
    """Contract for cleaning and sanitizing LLM text responses."""

    def clean(self, response: str, cleaners: Optional[List[Callable[[str], str]]] = None) -> str:
        """Removes Chain-of-Thought tags and applies custom cleaner filters."""
        ...


__all__ = [
    "ITemplateLoader",
    "IPromptBuilder",
    "IResponseSanitizer",
]
