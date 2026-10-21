# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Backward-compatibility bridge re-exporting handlers from `src.handlers`.
"""

from src.handlers.system_handler import SystemCommandHandler
from src.handlers.map_handler import MapCommandHandler
from src.handlers.source_handler import SourceCommandHandler
from src.handlers.database_handler import DatabaseCommandHandler
from src.handlers.dialog_handler import SystemDialogHandler
from src.handlers.handler_registry import register_default_command_handlers

__all__ = [
    "SystemCommandHandler",
    "MapCommandHandler",
    "SourceCommandHandler",
    "DatabaseCommandHandler",
    "SystemDialogHandler",
    "register_default_command_handlers",
]
