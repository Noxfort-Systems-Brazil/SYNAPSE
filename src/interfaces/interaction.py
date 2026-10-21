# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class IInteractionManager(Protocol):
    """
    Contract for UI interaction state (association mode, element selections).
    (SRP: Pure UI interaction state tracking).
    """

    def enter_association_mode(self, source_id: str) -> None:
        """Activate source-to-element association mode for a given source ID."""
        ...

    def exit_association_mode(self) -> None:
        """Deactivate association mode and clear current selection."""
        ...

    @property
    def is_active(self) -> bool:
        """Whether association mode is currently active."""
        ...

    @property
    def selected_id(self) -> Optional[str]:
        """Currently selected source ID awaiting element association."""
        ...
