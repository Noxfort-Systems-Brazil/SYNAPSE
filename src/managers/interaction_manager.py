# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Optional
from PyQt6.QtCore import QObject, pyqtSignal

from src.interfaces.interaction import IInteractionManager


class InteractionManager(QObject):
    """
    Presentation/UI State Manager for user modes and element selection.
    
    SOLID Architecture:
    - [SRP] Exclusively tracks transient GUI interaction state (e.g. association mode).
    - [DIP] Satisfies IInteractionManager protocol structurally.
    """
    mode_changed = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self._is_association_mode_active: bool = False
        self._selected_source_id: Optional[str] = None

    def enter_association_mode(self, source_id: str) -> None:
        """Activate association mode and select source ID."""
        self._is_association_mode_active = True
        self._selected_source_id = source_id
        self.mode_changed.emit(True)

    def exit_association_mode(self) -> None:
        """Deactivate association mode and clear selection."""
        self._is_association_mode_active = False
        self._selected_source_id = None
        self.mode_changed.emit(False)
    
    @property
    def is_active(self) -> bool:
        return self._is_association_mode_active
    
    @property
    def selected_id(self) -> Optional[str]:
        return self._selected_source_id


__all__ = ["InteractionManager"]
