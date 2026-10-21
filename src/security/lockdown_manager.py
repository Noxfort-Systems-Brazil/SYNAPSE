# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Lockdown and Intrusion Prevention Management (SOLID: SRP & OCP).
"""

import os
from typing import Callable, Optional
from src.security.interfaces import ILockdownManager
from src.utils.logging_setup import get_logger


class FileLockdownManager(ILockdownManager):
    """
    Manages rate-limiting and persistent lockdown using an on-disk flag file.
    Supports pluggable state persistence for the failed attempts counter.
    """

    def __init__(
        self,
        lockdown_file: str,
        max_failed_attempts: int = 3,
        attempts_getter: Optional[Callable[[], int]] = None,
        attempts_setter: Optional[Callable[[int], None]] = None,
    ):
        self.logger = get_logger("FileLockdownManager")
        self.lockdown_file = lockdown_file
        self.max_failed_attempts = max_failed_attempts
        self._attempts_getter = attempts_getter
        self._attempts_setter = attempts_setter
        self._memory_counter = 0

    def _get_attempts(self) -> int:
        if self._attempts_getter:
            try:
                return self._attempts_getter()
            except Exception as e:
                self.logger.warning(f"Error getting failed attempts counter: {e}")
        return self._memory_counter

    def _set_attempts(self, count: int) -> None:
        self._memory_counter = count
        if self._attempts_setter:
            try:
                self._attempts_setter(count)
            except Exception as e:
                self.logger.warning(f"Error persisting failed attempts counter: {e}")

    def is_lockdown(self) -> bool:
        """Returns True if the persistent lockdown flag file exists."""
        return os.path.exists(self.lockdown_file)

    def trigger_lockdown(self) -> None:
        """Creates the persistent lockdown flag file."""
        try:
            flag_dir = os.path.dirname(self.lockdown_file)
            if flag_dir:
                os.makedirs(flag_dir, exist_ok=True)
            with open(self.lockdown_file, "w", encoding="utf-8") as f:
                f.write("LOCKDOWN_ACTIVE")
            self.logger.critical(
                "🚨 SISTEMA ENTROU EM LOCKDOWN (Múltiplas tentativas de acesso inválidas)."
            )
        except Exception as e:
            self.logger.error(f"Failed to create lockdown flag: {e}")

    def clear_lockdown(self) -> None:
        """Removes the lockdown flag file and resets failed attempts counter."""
        if os.path.exists(self.lockdown_file):
            try:
                os.remove(self.lockdown_file)
            except Exception as e:
                self.logger.error(f"Failed to remove lockdown flag: {e}")

        self._set_attempts(0)
        self.logger.info("Lockdown removed and failed attempts counter reset.")

    def record_failed_attempt(self) -> bool:
        """
        Increments failed login attempts. Triggers lockdown when threshold is reached.
        Returns True if lockdown is active or was triggered during this call.
        """
        if self.is_lockdown():
            return True

        current = self._get_attempts() + 1
        self._set_attempts(current)
        self.logger.warning(
            f"Failed login attempt recorded. Total: {current}/{self.max_failed_attempts}"
        )

        if current >= self.max_failed_attempts:
            self.trigger_lockdown()
            return True

        return False

    def reset_attempts(self) -> None:
        """Resets failed attempts counter without touching lockdown flag."""
        if self._get_attempts() > 0:
            self._set_attempts(0)
