# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Configuration models and path resolution for the SYNAPSE logging infrastructure.
Adheres to SRP by encapsulating all logging configuration state and rules.
"""

import os
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Dict


LEVEL_MAP: Dict[str, int] = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "WARN": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

DEFAULT_NOISY_LIBS: List[str] = [
    "matplotlib", "PIL", "urllib3", "asyncio", "numba",
    "torch.distributed", "dateutil", "qdarktheme", "fontTools"
]


def resolve_log_directory(custom_dir: Optional[Path] = None) -> Path:
    """
    Resolves the central directory for SYNAPSE logs with fallback.
    Does not mutate system state unless requested during initialization.
    """
    if custom_dir:
        return custom_dir

    env_log_dir = os.environ.get("SYNAPSE_LOG_DIR")
    if env_log_dir:
        base_dir = Path(env_log_dir)
    else:
        from src.storage.path_scaffolder import PathScaffolder
        base_dir = Path(PathScaffolder().get_logs_path())

    try:
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir
    except Exception:
        fallback = Path.cwd() / "logs"
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


@dataclass
class LogConfig:
    """
    Immutable or extensible configuration container for the logging subsystem.
    """
    logger_name: str = "Synapse"
    console_level: int = logging.DEBUG
    file_level: int = logging.DEBUG
    redirect_streams: bool = True
    enable_excepthook: bool = True
    log_dir: Optional[Path] = None
    max_bytes: int = 50 * 1024 * 1024  # 50 MB
    backup_count: int = 5
    noisy_libs: List[str] = field(default_factory=lambda: list(DEFAULT_NOISY_LIBS))

    @classmethod
    def from_env(
        cls,
        logger_name: str = "Synapse",
        console_level: Optional[int] = None,
        file_level: int = logging.DEBUG,
        redirect_streams: Optional[bool] = None,
        log_dir: Optional[Path] = None
    ) -> "LogConfig":
        """
        Factory method to construct LogConfig reading defaults from environment variables.
        """
        env_level_str = os.environ.get("SYNAPSE_LOG_LEVEL", os.environ.get("LOG_LEVEL", "")).upper()
        resolved_console_level = console_level if console_level is not None else LEVEL_MAP.get(env_level_str, logging.DEBUG)

        if redirect_streams is None:
            resolved_redirect = os.environ.get("SYNAPSE_REDIRECT_STDOUT", "1").lower() in ("1", "true", "yes")
        else:
            resolved_redirect = redirect_streams

        return cls(
            logger_name=logger_name,
            console_level=resolved_console_level,
            file_level=file_level,
            redirect_streams=resolved_redirect,
            log_dir=log_dir or resolve_log_directory()
        )
