# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Dedicated Out-of-Process LLM Worker Entrypoint (multiprocessing spawn loop).
Delegates stateful model inference to LLMWorkerInstance (src.slm.llm_worker_instance).
"""

import os
import sys
import signal
import logging
from multiprocessing.connection import Connection

from src.slm.llm_worker_instance import LLMWorkerInstance

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(process)d] [%(levelname)s] [LLM.WorkerProcess] %(message)s",
)
logger = logging.getLogger("LLM.WorkerProcess")


def run_llm_worker(
    pipe_conn: Connection,
    model_id: str,
    device: str = "auto",
    gpu_layers: int = 16,
) -> None:
    """
    Subprocess main event loop receiving commands over multiprocessing.Pipe.
    """
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    logger.info(f"🚀 Isolated LLM Worker Process online (PID={os.getpid()}, model={model_id})")

    worker = LLMWorkerInstance(model_id=model_id, device=device, gpu_layers=gpu_layers)

    try:
        while True:
            try:
                msg = pipe_conn.recv()
            except (EOFError, KeyboardInterrupt):
                logger.info("Pipe closed or interrupted. Exiting LLM worker process.")
                break

            if not isinstance(msg, dict):
                continue

            msg_id = msg.get("id", "")
            cmd = msg.get("cmd", "")
            payload = msg.get("payload", {})

            try:
                if cmd == "ping":
                    pipe_conn.send({"id": msg_id, "success": True, "result": "pong", "pid": os.getpid()})

                elif cmd == "load_resources":
                    res = worker.load_resources(
                        device=payload.get("device"),
                        gpu_layers=payload.get("gpu_layers"),
                    )
                    pipe_conn.send({"id": msg_id, "success": True, "result": res})

                elif cmd == "unload_resources":
                    res = worker.unload_resources()
                    pipe_conn.send({"id": msg_id, "success": True, "result": res})

                elif cmd == "clear_cache":
                    res = worker.clear_cache()
                    pipe_conn.send({"id": msg_id, "success": True, "result": res})

                elif cmd == "generate_report":
                    text = worker.generate_report(payload)
                    pipe_conn.send({"id": msg_id, "success": True, "result": text})

                elif cmd == "generate_verdict":
                    text = worker.generate_verdict(payload)
                    pipe_conn.send({"id": msg_id, "success": True, "result": text})

                elif cmd == "shutdown":
                    logger.info("Shutdown command received. Cleaning up worker process.")
                    worker.unload_resources()
                    try:
                        pipe_conn.send({"id": msg_id, "success": True, "result": "shutdown_ok"})
                    except Exception:
                        pass
                    break

                else:
                    pipe_conn.send({"id": msg_id, "success": False, "error": f"Unknown command: {cmd}"})

            except Exception as cmd_err:
                logger.error(f"Error handling command '{cmd}': {cmd_err}", exc_info=True)
                pipe_conn.send({"id": msg_id, "success": False, "error": str(cmd_err)})

    finally:
        worker.unload_resources()
        try:
            pipe_conn.close()
        except Exception:
            pass
        logger.info(f"Isolated LLM Worker Process (PID={os.getpid()}) terminated cleanly.")
        sys.exit(0)
