# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import signal
import sys
import logging

logger = logging.getLogger(__name__)

def hard_kill(*args, exit_code: int = 0):
    """
    Performs an immediate hard kill on the current process and all of its child processes.
    Used for SIGINT (Ctrl+C) and explicit application exit from system tray or UI.
    """
    logger.info("[ProcessUtils] Hard kill triggered. Terminating process tree...")
    
    killed_with_psutil = False
    # 1. Terminate all child processes recursively
    try:
        import psutil
        current_process = psutil.Process(os.getpid())
        children = current_process.children(recursive=True)
        for child in children:
            try:
                child.kill()
            except Exception:
                pass
        killed_with_psutil = True
    except Exception as e:
        logger.warning(f"[ProcessUtils] Could not kill child processes via psutil: {e}")

    # 2. Fallback process group signal kill on Unix if psutil failed
    if not killed_with_psutil:
        try:
            os.killpg(os.getpgrp(), signal.SIGKILL)
        except Exception:
            pass

    # 3. Hard exit execution thread immediately
    os._exit(exit_code)
