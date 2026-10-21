# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Go Binary Lifecycle & Compilation Manager (SOLID: SRP).
Responsible exclusively for resolving, validating, and on-demand compiling of the Go gateway binary.
"""

import os
import shutil
import subprocess
from typing import Optional

from src.utils.logging_setup import get_logger

logger = get_logger("GoBinaryManager")


class GoBinaryManager:
    """
    Manages the executable binary artifact of the Go Ingestion Gateway (synapse-gateway).
    """

    def __init__(self, bin_path: Optional[str] = None):
        self.bin_path = bin_path or self.resolve_default_binary_path()

    @staticmethod
    def resolve_default_binary_path() -> str:
        """Finds the default compiled binary path relative to project root."""
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        return os.path.join(root_dir, "bin", "synapse-gateway")

    @classmethod
    def is_executable(cls, path: str) -> bool:
        """Returns True if the target path points to an executable binary file."""
        return os.path.isfile(path) and os.access(path, os.X_OK)

    @classmethod
    def compile_binary(cls, target_path: str) -> bool:
        """
        Invokes the Go build toolchain to compile cmd/gateway into target_path.
        Returns True if build succeeded.
        """
        go_compiler = shutil.which("go")
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        go_src = os.path.join(root_dir, "synapse-go")

        if not (go_compiler and os.path.isdir(go_src)):
            logger.warning(
                f"[GoBinaryManager] Go compiler ({go_compiler}) or source directory ({go_src}) "
                f"not found. Automatic compilation unavailable."
            )
            return False

        bin_dir = os.path.dirname(target_path)
        os.makedirs(bin_dir, exist_ok=True)

        logger.info(f"🔨 [GoBinaryManager] Compiling Go Gateway: {go_src} -> {target_path}...")
        try:
            subprocess.run(
                [go_compiler, "build", "-C", go_src, "-o", target_path, "./cmd/gateway"],
                capture_output=True,
                text=True,
                check=True,
            )
            logger.info("✅ [GoBinaryManager] Go Ingestion Gateway compiled successfully.")
            return True
        except subprocess.CalledProcessError as err:
            logger.error(f"❌ [GoBinaryManager] Compilation failed: {err.stderr}")
            return False

    def ensure_ready(self) -> bool:
        """
        Verifies if binary is present and executable; triggers compilation if absent.
        """
        if self.is_executable(self.bin_path):
            return True
        return self.compile_binary(self.bin_path)
