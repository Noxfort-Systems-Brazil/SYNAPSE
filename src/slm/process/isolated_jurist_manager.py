# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import threading
import multiprocessing
from multiprocessing.connection import Connection
from typing import Dict, Any, Optional

from src.utils.logging_setup import get_logger
from src.utils.model_paths import get_qwen_gguf_path
from src.slm.process.worker_supervisor import WorkerProcessSupervisor

logger = get_logger("SLM.IsolatedManager")


class IsolatedJuristManager:
    """
    Pure Orchestrator supervising the execution of the isolated LLM inference worker.

    Coordinates:
    - Worker process lifecycle delegation (WorkerProcessSupervisor)
    - Command sending and fault isolation
    - Synchronized high-level LLM calls (generate_report, generate_verdict)
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        default_device: str = "auto",
        default_gpu_layers: int = 16,
        command_timeout: float = 120.0,
    ):
        self.model_id = model_id or get_qwen_gguf_path()
        self.default_device = default_device
        self.default_gpu_layers = default_gpu_layers
        self.command_timeout = command_timeout
        self.is_gguf = str(self.model_id).endswith(".gguf")

        self._process: Optional[multiprocessing.Process] = None
        self._parent_conn: Optional[Connection] = None
        self._lock = threading.RLock()
        self._is_loaded = False

    @property
    def is_alive(self) -> bool:
        """Returns True if the worker process is currently running."""
        return self._process is not None and self._process.is_alive()

    @property
    def is_loaded(self) -> bool:
        """Returns True if the model is loaded and worker is alive."""
        return self.is_alive and self._is_loaded

    def _ensure_worker_started(self) -> None:
        """Spawns the dedicated worker process if not already active."""
        if self.is_alive:
            return

        self._cleanup_process()
        self._process, self._parent_conn = WorkerProcessSupervisor.spawn_worker(
            model_id=self.model_id,
            default_device=self.default_device,
            default_gpu_layers=self.default_gpu_layers,
        )

    def send_command(
        self,
        cmd: str,
        payload: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> Any:
        """Sends a synchronous command envelope to the isolated worker and awaits response."""
        timeout_val = timeout if timeout is not None else self.command_timeout

        with self._lock:
            self._ensure_worker_started()
            if not self._parent_conn or not self.is_alive:
                raise RuntimeError("Failed to establish IPC connection with isolated LLM worker process.")

            try:
                return WorkerProcessSupervisor.send_and_wait(
                    parent_conn=self._parent_conn,
                    process=self._process,
                    cmd=cmd,
                    payload=payload,
                    timeout=timeout_val,
                )
            except Exception:
                self._cleanup_process(force=True)
                raise

    def load_resources(self, device: str = "auto", gpu_layers: int = 16) -> None:
        """Instructs worker to load model weights."""
        with self._lock:
            try:
                res = self.send_command(
                    "load_resources",
                    payload={"device": device, "gpu_layers": gpu_layers},
                    timeout=45.0,
                )
                self._is_loaded = True
                logger.info(f"Isolated Jurist resources loaded: {res}")
            except Exception as e:
                logger.error(f"Error loading resources in isolated worker: {e}", exc_info=True)
                self._is_loaded = False
                raise

    def unload_resources(self) -> None:
        """Instructs worker to unload model weights and terminates process to guarantee 0 bytes VRAM."""
        with self._lock:
            if not self.is_alive:
                self._is_loaded = False
                return

            try:
                self.send_command("unload_resources", timeout=5.0)
            except Exception as e:
                logger.warning(f"Error while sending unload command to worker: {e}")
            finally:
                self._is_loaded = False
                self.shutdown()

    def generate_report(
        self,
        tensor_data: Dict[str, Any],
        timestamp: str = "",
        locale: str = "pt_BR",
        target: str = "XAI_Attribution",
        auto_unload: bool = True,
        timeout: float = 120.0,
        **kwargs: Any,
    ) -> str:
        """Executes XAI narrative report synthesis in the isolated process."""
        payload = {
            "tensor_data": tensor_data,
            "timestamp": timestamp,
            "locale": locale,
            "target": target,
            "auto_unload": auto_unload,
            **kwargs,
        }
        with self._lock:
            try:
                result = self.send_command("generate_report", payload=payload, timeout=timeout)
                if auto_unload:
                    self.shutdown()
                return str(result)
            except Exception as e:
                logger.error(f"Isolated report generation failed: {e}")
                if auto_unload:
                    self.shutdown()
                return f"Erro: Inferência da LLM em processo isolado falhou: {e}"

    def generate(
        self,
        context_data: Dict[str, Any],
        auto_unload: bool = False,
        timeout: float = 120.0,
    ) -> str:
        """Executes general verdict generation in the isolated process."""
        payload = dict(context_data)
        payload["auto_unload"] = auto_unload

        with self._lock:
            try:
                result = self.send_command("generate_verdict", payload=payload, timeout=timeout)
                if auto_unload:
                    self.shutdown()
                return str(result)
            except Exception as e:
                logger.error(f"Isolated verdict generation failed: {e}")
                if auto_unload:
                    self.shutdown()
                return f"Erro: Inferência da LLM em processo isolado falhou: {e}"

    def shutdown(self) -> None:
        """Gracefully stops the worker process and frees all OS resources."""
        with self._lock:
            self._cleanup_process(force=False)

    def _cleanup_process(self, force: bool = False) -> None:
        """Internal helper to shut down and clean up worker process and pipe."""
        with self._lock:
            WorkerProcessSupervisor.cleanup(self._parent_conn, self._process, force=force)
            self._parent_conn = None
            self._process = None
            self._is_loaded = False
