# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
OS Subprocess & Anonymous Pipe Lifecycle (SOLID: SRP).
Responsible strictly for low-level process execution, PID management,
line-buffered pipe I/O, and safe termination.
"""

import subprocess
import threading
from typing import IO, List, Optional

from src.utils.logging_setup import get_logger

logger = get_logger("GoPipeProcess")


class GoPipeProcess:
    """
    Encapsulates the low-level operating system process and standard I/O pipes.
    """

    def __init__(self, bin_path: str):
        self.bin_path = bin_path
        self._process: Optional[subprocess.Popen] = None
        self._write_lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        return self._process is not None and self._process.poll() is None

    @property
    def stdout(self) -> Optional[IO[str]]:
        return self._process.stdout if self._process else None

    @property
    def stderr(self) -> Optional[IO[str]]:
        return self._process.stderr if self._process else None

    @property
    def pid(self) -> Optional[int]:
        return self._process.pid if self._process else None

    def spawn(self, extra_args: Optional[List[str]] = None) -> bool:
        """Launches the subprocess with anonymous pipes bound for line-buffered I/O."""
        if self.is_running:
            logger.warning("[GoPipeProcess] Subprocess is already running.")
            return True

        cmd = [self.bin_path]
        if extra_args:
            cmd.extend(extra_args)

        logger.info(f"🚀 [GoPipeProcess] Spawning daemon ({' '.join(cmd)}) with OS anonymous pipes...")
        try:
            self._process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line-buffered
            )
            return True
        except Exception as e:
            logger.error(f"❌ [GoPipeProcess] Failed to spawn process: {e}", exc_info=True)
            self._process = None
            return False

    def write_line(self, line: str) -> bool:
        """Thread-safe write of a newline-terminated string to the process STDIN pipe."""
        if not self.is_running or not self._process or not self._process.stdin:
            return False

        with self._write_lock:
            try:
                if not line.endswith("\n"):
                    line += "\n"
                self._process.stdin.write(line)
                self._process.stdin.flush()
                return True
            except (BrokenPipeError, OSError) as err:
                logger.debug(f"[GoPipeProcess] STDIN pipe broken: {err}")
                return False

    def close_stdin(self) -> None:
        """Closes the STDIN pipe to signal EOF to the child process."""
        if self._process and self._process.stdin:
            try:
                self._process.stdin.close()
            except Exception:
                pass

    def terminate_gracefully(self, timeout: float = 2.0) -> None:
        """Waits for process termination; falls back to SIGTERM and SIGKILL if needed."""
        if not self._process or self._process.poll() is not None:
            self._process = None
            return

        try:
            self._process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            logger.warning(f"[GoPipeProcess] Subprocess PID {self.pid} did not exit in {timeout}s. Terminating...")
            try:
                self._process.terminate()
                self._process.wait(timeout=1.0)
            except Exception:
                logger.warning(f"[GoPipeProcess] Subprocess PID {self.pid} forced kill.")
                self._process.kill()
        finally:
            self._process = None
