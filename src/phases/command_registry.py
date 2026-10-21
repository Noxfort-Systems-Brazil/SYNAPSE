# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import logging
from typing import Callable, Dict, Optional

logger = logging.getLogger(__name__)


class CommandRegistry:
    """
    Dynamic command dispatcher (Open/Closed Principle).

    Instead of a growing if/elif chain, commands are registered as
    (name → handler) pairs. The execute() method performs a single
    dict lookup — O(1) dispatch with zero conditional branches.

    Usage:
        registry = CommandRegistry()
        registry.register("run_cycle", engine.run_global_cycle)
        registry.execute("run_cycle")
    """

    def __init__(self):
        self._handlers: Dict[str, Callable] = {}

    def register(self, command_type: str, handler: Callable) -> None:
        """
        Registers a handler for the given command type.

        Args:
            command_type: Unique string key (e.g. "run_cycle").
            handler: Callable that accepts an optional payload argument.
                     For payload-less commands, the payload will be None.
        """
        self._handlers[command_type] = handler
        logger.debug(f"[CommandRegistry] Registered: '{command_type}'")

    def unregister(self, command_type: str) -> None:
        """Removes a previously registered command handler."""
        self._handlers.pop(command_type, None)

    def execute(self, command_type: str, payload: object = None) -> None:
        """
        Dispatches a command to its registered handler.

        Args:
            command_type: The command key to look up.
            payload: Optional data to pass to the handler.
        """
        handler = self._handlers.get(command_type)
        if handler is None:
            logger.warning(
                f"[CommandRegistry] Unknown command: '{command_type}' "
                f"(registered: {list(self._handlers.keys())})"
            )
            return

        # Invoke: handlers that accept payload receive it;
        # handlers that don't (zero-arg) are called without it.
        try:
            if payload is not None:
                handler(payload)
            else:
                handler()
        except TypeError:
            # Fallback: handler signature doesn't match — try without payload
            handler()

    def clear(self) -> None:
        """Removes all registered handlers."""
        self._handlers.clear()

    @property
    def registered_commands(self) -> list:
        """Returns a list of currently registered command names."""
        return list(self._handlers.keys())
