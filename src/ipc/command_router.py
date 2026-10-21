# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
IPC Command Router and Registry (SOLID: SRP & OCP).

Provides an extensible registry for IPC action handlers.
Open for extension by registering new command handlers without modifying the router or daemon core.
"""

from typing import Callable, Dict, Any, Optional
import inspect

from src.ipc.ipc_protocol import IpcMessage, IpcResponse
from src.utils.logging_setup import get_logger


# Type alias for the responder callback: (success, result, error) -> None
Responder = Callable[[bool, Any, Optional[str]], None]
CommandHandler = Callable[[IpcMessage, Responder], Any]


class IpcCommandRouter:
    """
    Extensible command registry and dispatcher for IPC actions.
    """

    def __init__(self):
        self.logger = get_logger("IpcCommandRouter")
        self._handlers: Dict[str, CommandHandler] = {}

    def register(self, action: str, handler: CommandHandler) -> None:
        """Registers a handler for a specific action name."""
        self._handlers[action] = handler

    def unregister(self, action: str) -> None:
        """Removes a handler for an action."""
        self._handlers.pop(action, None)

    def has_action(self, action: str) -> bool:
        """Checks if an action handler is registered."""
        return action in self._handlers

    def dispatch(
        self,
        msg: IpcMessage,
        response_emitter: Callable[[IpcResponse], None],
    ) -> None:
        """
        Dispatches an incoming message to its registered action handler.
        Handles synchronous returns, explicit callback responses, and unhandled errors.
        """
        action = msg.action
        msg_id = msg.id

        if action not in self._handlers:
            self.logger.warning(f"[IPC Router] ⚠️ Ação IPC não reconhecida: '{action}'")
            response_emitter(
                IpcResponse(id=msg_id, success=False, error=f"Unknown action: {action}")
            )
            return

        handler = self._handlers[action]

        def responder(success: bool, result: Any = None, error: Optional[str] = None) -> None:
            if not success:
                self.logger.error(f"[IPC Router] ❌ Resposta com falha para '{action}' (id={msg_id}): {error}")
            response_emitter(
                IpcResponse(id=msg_id, success=success, result=result, error=error)
            )

        try:
            # Inspect handler signature to support both (msg, responder) and (msg)
            sig = inspect.signature(handler)
            num_params = len(sig.parameters)

            if num_params >= 2:
                res = handler(msg, responder)
            else:
                res = handler(msg)

            # If the handler returned a direct value synchronously (and did not return None)
            if res is not None:
                if isinstance(res, IpcResponse):
                    response_emitter(res)
                else:
                    responder(True, res)

        except Exception as ex:
            self.logger.error(f"[IPC Router] ❌ Exceção não tratada ao executar ação '{action}': {ex}", exc_info=True)
            responder(False, error=f"Erro interno ao executar '{action}': {ex}")
