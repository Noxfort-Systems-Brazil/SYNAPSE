# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Pure Orchestrator / Backward Compatibility Facade for SYNAPSE Logging.
Delegates all formatting, handlers, interceptors, and configuration to src.logging.
"""

import logging
from typing import Optional
from pathlib import Path

from src.logging.config import LogConfig
from src.logging.formatters import DetailedColoredFormatter, DetailedFileFormatter
from src.logging.interceptors import StreamToLogger
from src.logging.facade import (
    setup_logging,
    get_logger,
    set_global_level,
    get_log_dir,
    get_session_log_path,
)


def setup_logger(
    logger_name: str = "Synapse",
    console_level: Optional[int] = None,
    file_level: int = logging.DEBUG,
    redirect_streams: Optional[bool] = None
) -> logging.Logger:
    """
    Backward-compatible orchestration wrapper for setup_logging.
    """
    config = LogConfig.from_env(
        logger_name=logger_name,
        console_level=console_level,
        file_level=file_level,
        redirect_streams=redirect_streams
    )
    return setup_logging(config)


# Exported singleton instance for legacy imports
logger = setup_logger()

__all__ = [
    "setup_logger",
    "setup_logging",
    "get_logger",
    "set_global_level",
    "get_log_dir",
    "get_session_log_path",
    "DetailedColoredFormatter",
    "DetailedFileFormatter",
    "StreamToLogger",
    "logger",
]
