# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import time
import uuid
import logging
import multiprocessing
from multiprocessing.connection import Connection
from typing import Dict, Any, Optional, Tuple

from src.slm.process.llm_worker_process import run_llm_worker

logger = logging.getLogger("SLM.WorkerSupervisor")


class WorkerProcessSupervisor:
    """Manages the creation, communication and graceful termination of worker subprocesses."""

    @staticmethod
    def spawn_worker(
        model_id: str,
        default_device: str,
        default_gpu_layers: int
    ) -> Tuple[multiprocessing.Process, Connection]:
        """Spawns an isolated LLM worker process via spawn context."""
        logger.info(f"Spawning isolated LLM worker process for model: {model_id}")
        ctx = multiprocessing.get_context("spawn")
        parent_conn, child_conn = ctx.Pipe(duplex=True)

        process = ctx.Process(
            target=run_llm_worker,
            args=(child_conn, model_id, default_device, default_gpu_layers),
            daemon=True,
            name="Synapse-LLM-Worker",
        )
        process.start()

        try:
            child_conn.close()
        except Exception:
            pass

        logger.info(f"Isolated LLM Worker started with PID={process.pid}")
        return process, parent_conn

    @staticmethod
    def send_and_wait(
        parent_conn: Connection,
        process: multiprocessing.Process,
        cmd: str,
        payload: Optional[Dict[str, Any]],
        timeout: float
    ) -> Any:
        """Sends command envelope over pipe and polls for response with timeout."""
        req_id = str(uuid.uuid4())
        envelope = {"id": req_id, "cmd": cmd, "payload": payload or {}}

        try:
            parent_conn.send(envelope)
        except Exception as e_send:
            logger.error(f"Failed to send command '{cmd}' over pipe: {e_send}")
            raise RuntimeError(f"IPC Send failed: {e_send}") from e_send

        start_time = time.time()
        poll_interval = 0.1

        while time.time() - start_time < timeout:
            if not process.is_alive():
                exit_code = process.exitcode if process else -1
                raise RuntimeError(f"Isolated LLM Worker process died unexpectedly (exitcode={exit_code}).")

            try:
                if parent_conn.poll(poll_interval):
                    resp = parent_conn.recv()
                    if isinstance(resp, dict) and resp.get("id") == req_id:
                        if resp.get("success"):
                            return resp.get("result")
                        raise RuntimeError(resp.get("error", "Unknown worker error"))
            except (EOFError, BrokenPipeError, ConnectionResetError, ConnectionError, OSError) as e_pipe:
                raise RuntimeError(f"IPC Pipe broken during command '{cmd}': {e_pipe}") from e_pipe

        logger.error(f"Command '{cmd}' timed out after {timeout:.1f}s.")
        raise TimeoutError(f"Isolated LLM inference timed out after {timeout}s.")

    @staticmethod
    def cleanup(
        parent_conn: Optional[Connection],
        process: Optional[multiprocessing.Process],
        force: bool = False
    ) -> None:
        """Shuts down and cleans up worker process and pipe."""
        if parent_conn:
            if not force and process and process.is_alive():
                try:
                    parent_conn.send({"id": "exit", "cmd": "shutdown", "payload": {}})
                    if parent_conn.poll(0.2):
                        parent_conn.recv()
                except Exception:
                    pass
            try:
                parent_conn.close()
            except Exception:
                pass

        if process is not None:
            if process.is_alive():
                try:
                    process.join(timeout=1.0)
                    if process.is_alive():
                        process.terminate()
                        process.join(timeout=1.0)
                        if process.is_alive():
                            process.kill()
                except Exception:
                    pass
            logger.info("Isolated LLM worker process cleaned up.")
