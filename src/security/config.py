# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Security Configuration & OS Environment Resolution (SOLID: SRP & DIP).
"""

import os
import sys
import hashlib
from dataclasses import dataclass
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def get_user_config_dir() -> str:
    """
    Returns the persistent user configuration directory following OS standards.
    Supports SYNAPSE_CONFIG_DIR environment override.
    """
    env_dir = os.environ.get("SYNAPSE_CONFIG_DIR")
    if env_dir:
        os.makedirs(env_dir, exist_ok=True)
        return env_dir

    if sys.platform.startswith("win"):
        base_dir = os.environ.get("APPDATA") or os.path.expanduser("~/AppData/Roaming")
    elif sys.platform.startswith("darwin"):
        base_dir = os.path.expanduser("~/Library/Application Support")
    else:
        # Linux / Unix XDG standard
        base_dir = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")

    config_dir = os.path.join(base_dir, "synapse")
    os.makedirs(config_dir, exist_ok=True)
    return config_dir


@dataclass
class SecurityConfig:
    """Immutable configuration parameters for security and master superuser fallback."""

    config_dir: str
    security_file: str
    lockdown_file: str
    default_user: str = "admin"
    default_hash: str = "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"  # sha256("admin")
    master_user: str = "admin"
    master_hash: str = "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"
    max_failed_attempts: int = 3

    @classmethod
    def from_env(cls, config_dir: Optional[str] = None) -> "SecurityConfig":
        """Factory method to construct SecurityConfig from current environment variables."""
        target_dir = config_dir or get_user_config_dir()
        os.makedirs(target_dir, exist_ok=True)

        security_file = os.path.join(target_dir, "security.json")
        lockdown_file = os.path.join(target_dir, "lockdown.flag")

        default_user = "admin"
        default_hash = "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918"

        master_user = os.environ.get("SYNAPSE_SUPERUSER", default_user)
        custom_password = os.environ.get("SYNAPSE_SUPERUSER_PASSWORD")
        if custom_password:
            master_hash = hashlib.sha256(custom_password.encode("utf-8")).hexdigest()
        else:
            master_hash = os.environ.get("SYNAPSE_SUPERUSER_HASH", default_hash)

        return cls(
            config_dir=target_dir,
            security_file=security_file,
            lockdown_file=lockdown_file,
            default_user=default_user,
            default_hash=default_hash,
            master_user=master_user,
            master_hash=master_hash,
            max_failed_attempts=3,
        )
