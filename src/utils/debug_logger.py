# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import atexit
import json
import logging
import queue
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime, date
from typing import Dict, Any, Optional
from src.utils.logging_setup import get_log_dir


def _create_debug_logger(name: str, subfolder: str, prefix: str) -> logging.Logger:
    """
    Creates an independent rotating file logger under <synapse_log_dir>/<subfolder>/.
    
    Each logger:
    - Writes to a session-based file: <prefix>_YYYY-MM-DD_HH-MM-SS.log
    - Uses RotatingFileHandler (max 20MB, 5 backups)
    - Has its own isolated hierarchy (no propagation to root)
    - Includes high-resolution timestamps, thread info, and file:line correlation
    """
    base_dir = get_log_dir() / subfolder
    
    try:
        base_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"[DEBUG_LOGGER] Warning: Could not create {base_dir}: {e}")
        base_dir = Path.cwd() / "logs" / subfolder
        base_dir.mkdir(parents=True, exist_ok=True)
    
    session_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = base_dir / f"{prefix}_{session_id}.log"
    
    dbg_logger = logging.getLogger(f"Synapse.debug.{name}")
    dbg_logger.setLevel(logging.DEBUG)
    dbg_logger.propagate = False  # Isolate from root/SYNAPSE logger
    
    # Avoid duplicate handlers on reimport
    if dbg_logger.hasHandlers():
        dbg_logger.handlers.clear()
    
    # High-resolution formatter with milliseconds for cross-log correlation
    formatter = logging.Formatter(
        '%(asctime)s.%(msecs)03d | %(levelname)-7s | [%(process)d:%(threadName)s] | %(filename)s:%(lineno)d (%(funcName)s) | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    handler = RotatingFileHandler(
        log_file,
        maxBytes=20 * 1024 * 1024,  # 20 MB
        backupCount=5,
        encoding='utf-8'
    )
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    dbg_logger.addHandler(handler)
    
    dbg_logger.info(f"--- SESSION STARTED: {log_file} ---")
    
    return dbg_logger


def _json_default(obj: Any) -> Any:
    """Fallback serializer for objects like NumPy arrays, tensors, and dates."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    tolist_fn = getattr(obj, "tolist", None)
    if callable(tolist_fn):
        return tolist_fn()
    item_fn = getattr(obj, "item", None)
    if callable(item_fn):
        return item_fn()
    return str(obj)


class JsonLinesLogger:
    """
    Thread-safe, size-bounded rotating JSON Lines (JSONL) logger for high-frequency telemetry.
    Supports optional non-blocking background queue execution to keep the 1 Hz real-time loop stall-free.
    """

    def __init__(
        self,
        subfolder: str,
        prefix: str,
        max_bytes: int = 20 * 1024 * 1024,
        backup_count: int = 3,
        async_mode: bool = False,
        max_queue_size: int = 256,
    ):
        self.subfolder = subfolder
        self.prefix = prefix
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.async_mode = async_mode
        self._lock = threading.Lock()
        self._file_handle = None
        self._current_file: Optional[Path] = None
        self._written_bytes: int = 0
        self._session_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self._queue: Optional[queue.Queue] = queue.Queue(maxsize=max_queue_size) if async_mode else None
        self._worker: Optional[threading.Thread] = None
        self._init_file()
        if self.async_mode:
            self._ensure_worker()
            atexit.register(self.close)

    def _init_file(self) -> None:
        base_dir = get_log_dir() / self.subfolder
        try:
            base_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            base_dir = Path.cwd() / "logs" / self.subfolder
            base_dir.mkdir(parents=True, exist_ok=True)

        self._current_file = base_dir / f"{self.prefix}_{self._session_id}.jsonl"
        self._file_handle = open(self._current_file, "a", encoding="utf-8", buffering=1)
        try:
            self._written_bytes = self._current_file.stat().st_size
        except Exception:
            self._written_bytes = 0

    def _rotate_locked(self) -> None:
        if self._current_file is None:
            return
        if self._file_handle and not self._file_handle.closed:
            self._file_handle.close()
        if self.backup_count <= 0:
            self._file_handle = open(self._current_file, "w", encoding="utf-8", buffering=1)
            self._written_bytes = 0
            return
        oldest = Path(f"{self._current_file}.{self.backup_count}")
        if oldest.exists():
            oldest.unlink(missing_ok=True)
        for idx in range(self.backup_count - 1, 0, -1):
            src = Path(f"{self._current_file}.{idx}")
            if src.exists():
                src.replace(Path(f"{self._current_file}.{idx + 1}"))
        if self._current_file.exists():
            self._current_file.replace(Path(f"{self._current_file}.1"))
        self._file_handle = open(self._current_file, "a", encoding="utf-8", buffering=1)
        self._written_bytes = 0

    def _write_record(self, data: Dict[str, Any]) -> None:
        try:
            line = json.dumps(data, ensure_ascii=False, default=_json_default) + "\n"
            encoded_len = len(line.encode("utf-8"))
            with self._lock:
                if self._file_handle is None or self._file_handle.closed:
                    self._init_file()
                if self.max_bytes > 0 and self._written_bytes > 0 and (self._written_bytes + encoded_len) > self.max_bytes:
                    self._rotate_locked()
                self._file_handle.write(line)
                self._written_bytes += encoded_len
        except Exception:
            pass

    def _ensure_worker(self) -> None:
        if self._queue is not None and (self._worker is None or not self._worker.is_alive()):
            self._worker = threading.Thread(
                target=self._worker_loop, daemon=True, name=f"JsonlLogger-{self.prefix}"
            )
            self._worker.start()

    def _worker_loop(self) -> None:
        assert self._queue is not None
        while True:
            item = self._queue.get()
            try:
                if item is None:
                    break
                if isinstance(item, threading.Event):
                    with self._lock:
                        if self._file_handle and not self._file_handle.closed:
                            self._file_handle.flush()
                    item.set()
                elif isinstance(item, dict):
                    self._write_record(item)
            finally:
                self._queue.task_done()

    def log(self, data: Dict[str, Any]) -> None:
        """Appends a single JSON line thread-safely (non-blocking when async_mode=True)."""
        if self.async_mode and self._queue is not None:
            try:
                self._ensure_worker()
                self._queue.put_nowait(data)
            except queue.Full:
                pass
            return
        self._write_record(data)

    def flush(self, timeout: float = 1.5) -> None:
        """Drains pending async records and flushes OS buffers."""
        if self.async_mode and self._queue is not None and self._worker is not None and self._worker.is_alive():
            done_evt = threading.Event()
            try:
                self._queue.put(done_evt, timeout=timeout)
                done_evt.wait(timeout=timeout)
            except Exception:
                pass
        with self._lock:
            if self._file_handle and not self._file_handle.closed:
                try:
                    self._file_handle.flush()
                except Exception:
                    pass

    @property
    def file_path(self) -> Optional[Path]:
        return self._current_file

    def close(self) -> None:
        if self.async_mode and self._queue is not None and self._worker is not None and self._worker.is_alive():
            try:
                self._queue.put(None, timeout=1.5)
                self._worker.join(timeout=1.5)
            except Exception:
                pass
            self._worker = None
        with self._lock:
            if self._file_handle and not self._file_handle.closed:
                try:
                    self._file_handle.close()
                except Exception:
                    pass
                self._file_handle = None


# ============================================================================
# EXPORTED SINGLETON LOGGERS
# ============================================================================

# Log 1: Carina Data Flow (KSE packet build + gRPC serialization + transmission)
# Records: KSE_BUILD, GRPC_FRAME, GRPC_SCENARIO, GRPC_COMMAND
carina_logger = _create_debug_logger("carina", "carina", "carina")

# Log 2: Neural Network Performance Metrics
# Records: CYCLE (per-stage timing), GLOBAL_CYCLE (total engine cycle)
perf_logger = _create_debug_logger("performance", "performance", "perf")

# Structured JSONL Dumps: Input data arriving at KSE vs Output traffic packets sent to CARINA
carina_input_logger = JsonLinesLogger("carina", "carina_input", async_mode=True)
carina_output_logger = JsonLinesLogger("carina", "carina_output", async_mode=True)

