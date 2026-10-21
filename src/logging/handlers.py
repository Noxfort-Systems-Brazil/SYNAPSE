# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Handler factory implementations for console and rotating file logs.
Adheres to SRP and DIP by isolating handler instantiation and configuration.
"""

import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional
from src.logging.formatters import DetailedColoredFormatter, DetailedFileFormatter


def create_console_handler(
    level: int = logging.DEBUG,
    formatter: Optional[logging.Formatter] = None
) -> logging.StreamHandler:
    """
    Creates and configures a console StreamHandler targeting standard stderr.
    Using stderr ensures real-time visibility in the terminal without corrupting
    stdout IPC streams used for GUI communication.
    """
    target_stream = sys.__stderr__ if sys.__stderr__ is not None else sys.stderr
    handler = logging.StreamHandler(target_stream)
    handler.setLevel(level)
    handler.setFormatter(formatter or DetailedColoredFormatter())
    return handler


def create_rotating_file_handler(
    file_path: Path,
    level: int = logging.DEBUG,
    formatter: Optional[logging.Formatter] = None,
    max_bytes: int = 50 * 1024 * 1024,
    backup_count: int = 5
) -> Optional[RotatingFileHandler]:
    """
    Creates and configures a RotatingFileHandler targeting a specific file path.
    Ensures parent directory existence safely.
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            file_path,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
        handler.setLevel(level)
        handler.setFormatter(formatter or DetailedFileFormatter())
        return handler
    except Exception as e:
        print(f"[LoggingHandlers] Warning: Could not create file handler at {file_path}: {e}")
        return None
