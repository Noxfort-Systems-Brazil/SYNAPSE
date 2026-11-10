# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import sys
import gc
import ctypes
import warnings
import pytest
from unittest.mock import MagicMock

# --- Global Environment & Thread Constraints for Safe Test Execution ---
# Restrict glibc memory arenas to prevent multi-threaded malloc memory retention
os.environ.setdefault("MALLOC_ARENA_MAX", "2")
# Prevent torch._inductor from spawning dozens of compiler worker processes
os.environ.setdefault("TORCHINDUCTOR_COMPILE_THREADS", "1")
os.environ.setdefault("TORCHDYNAMO_DISABLE", "0")
# Limit thread pools to avoid excessive memory and CPU contention
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "max_split_size_mb:64")


def _get_process_rss_mb() -> float:
    """Returns current process Resident Set Size in megabytes."""
    try:
        with open("/proc/self/status", "r") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return float(line.split()[1]) / 1024.0
    except Exception:
        pass
    try:
        import psutil
        return psutil.Process().memory_info().rss / (1024.0 * 1024.0)
    except Exception:
        return 0.0


def _get_system_available_ram_mb() -> float:
    """Returns available physical RAM on the system in megabytes."""
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    return float(line.split()[1]) / 1024.0
    except Exception:
        pass
    try:
        import psutil
        return psutil.virtual_memory().available / (1024.0 * 1024.0)
    except Exception:
        return 999999.0


def _trim_memory():
    """Forces aggressive GC, CUDA cache cleanup, and releases glibc arenas back to the OS."""
    gc.collect()
    if "torch" in sys.modules:
        try:
            torch_mod = sys.modules["torch"]
            if hasattr(torch_mod, "cuda") and torch_mod.cuda.is_available():
                torch_mod.cuda.empty_cache()
                if hasattr(torch_mod.cuda, "ipc_collect"):
                    torch_mod.cuda.ipc_collect()
        except Exception:
            pass
    try:
        libc = ctypes.CDLL("libc.so.6")
        libc.malloc_trim(0)
    except Exception:
        pass


def pytest_sessionstart(session):
    """Initializes resource boundaries and thread constraints for test execution."""
    try:
        import torch
        torch_threads = int(os.environ.get("SYNAPSE_TEST_TORCH_THREADS", "1"))
        torch.set_num_threads(torch_threads)
        if hasattr(torch, "set_num_interop_threads"):
            try:
                torch.set_num_interop_threads(1)
            except RuntimeError:
                pass
    except ImportError:
        pass


def pytest_runtest_setup(item):
    """Pre-test watchdog: checks available system RAM and process ceiling."""
    if "heavy_memory" in item.keywords and os.environ.get("SYNAPSE_SKIP_HEAVY_TESTS", "1") == "1":
        pytest.skip("Skipped heavy_memory test due to SYNAPSE_SKIP_HEAVY_TESTS=1.")

    # 1. System-wide Available RAM Watchdog (prevents OS freeze/swap lockup)
    min_free_mb = float(os.environ.get("SYNAPSE_TEST_MIN_FREE_RAM_MB", "2048.0"))
    avail_mb = _get_system_available_ram_mb()
    if avail_mb < min_free_mb:
        _trim_memory()
        avail_mb = _get_system_available_ram_mb()
        if avail_mb < min_free_mb:
            pytest.exit(
                f"\n[FATAL RAM GUARD] Available system RAM ({avail_mb:.0f} MB) is below safe minimum ({min_free_mb:.0f} MB). "
                f"Aborted test suite to prevent machine freeze.",
                returncode=1
            )

    # 2. Process RSS Ceiling Guard
    max_rss_mb = float(os.environ.get("SYNAPSE_TEST_MAX_RSS_MB", "3072.0"))
    curr_rss_mb = _get_process_rss_mb()
    if max_rss_mb > 0 and curr_rss_mb > max_rss_mb:
        _trim_memory()
        curr_rss_mb = _get_process_rss_mb()
        if curr_rss_mb > max_rss_mb:
            pytest.exit(
                f"\n[FATAL RAM GUARD] Test process RSS ({curr_rss_mb:.0f} MB) exceeded ceiling ({max_rss_mb:.0f} MB). "
                f"Aborted test suite immediately to prevent memory explosion.",
                returncode=1
            )

    item._start_rss_mb = curr_rss_mb


def pytest_runtest_teardown(item, nextitem):
    """Post-test reclamation: forces GC, drops glibc arenas, and enforces memory boundaries."""
    _trim_memory()

    max_rss_mb = float(os.environ.get("SYNAPSE_TEST_MAX_RSS_MB", "3072.0"))
    curr_rss_mb = _get_process_rss_mb()
    if max_rss_mb > 0 and curr_rss_mb > max_rss_mb:
        _trim_memory()
        curr_rss_mb = _get_process_rss_mb()
        if curr_rss_mb > max_rss_mb:
            pytest.exit(
                f"\n[FATAL RAM GUARD] Test '{item.nodeid}' caused process RSS ({curr_rss_mb:.0f} MB) "
                f"to exceed safe limit ({max_rss_mb:.0f} MB). Aborted test suite to protect system stability.",
                returncode=1
            )

    min_free_mb = float(os.environ.get("SYNAPSE_TEST_MIN_FREE_RAM_MB", "2048.0"))
    avail_mb = _get_system_available_ram_mb()
    if avail_mb < min_free_mb:
        _trim_memory()
        avail_mb = _get_system_available_ram_mb()
        if avail_mb < min_free_mb:
            pytest.exit(
                f"\n[FATAL RAM GUARD] Available system RAM ({avail_mb:.0f} MB) is below safe minimum ({min_free_mb:.0f} MB). "
                f"Aborted test suite to prevent OS freeze/swap lockup.",
                returncode=1
            )

    start_rss = getattr(item, "_start_rss_mb", None)
    if start_rss is not None:
        delta = curr_rss_mb - start_rss
        if delta > 250.0:
            sys.stderr.write(
                f"\n[RAM WARNING] Test '{item.nodeid}' increased RSS by +{delta:.1f} MB (Current RSS: {curr_rss_mb:.1f} MB)\n"
            )


from src.domain.app_state import AppState
from src.managers.storage_manager import StorageManager

@pytest.fixture
def mock_storage_manager():
    """
    Returns a mocked StorageManager that avoids creating real directories.
    """
    sm = MagicMock()
    sm.get_datalake_base_path.return_value = "/tmp/mock/datalake/base"
    sm.get_datalake_golden_path.return_value = "/tmp/mock/datalake/golden"
    sm.get_checkpoint_path.return_value = "/tmp/mock/Checkpoint"
    sm.save_model_checkpoint.return_value = "/tmp/mock/Checkpoint/model.pth"
    sm.is_connected = True
    return sm

@pytest.fixture
def mock_app_state():
    """
    Returns a mocked AppState to avoid complex UI/Topology setups during unit tests.
    """
    app_state = MagicMock(spec=AppState)
    
    # Mocking essential signals to allow .connect() checks
    class MockSignal:
        def connect(self, *args, **kwargs): pass
        def emit(self, *args, **kwargs): pass
        
    app_state.map_data_loaded = MockSignal()
    app_state.association_mode_changed = MockSignal()
    app_state.data_association_changed = MockSignal()
    app_state.data_source_added = MockSignal()
    app_state.data_source_removed = MockSignal()
    app_state.source_origin_toggled = MockSignal()
    
    app_state.get_all_data_sources.return_value = []
    app_state.get_map_source_path.return_value = None
    return app_state


@pytest.fixture(autouse=True)
def isolate_sources_json(tmp_path, monkeypatch):
    """Prevents tests from writing or reading user's real ~/Documentos/Synapse/config/sources.json."""
    mock_sources_path = str(tmp_path / "test_sources.json")
    monkeypatch.setattr(
        "src.infrastructure.json_source_storage.JsonSourceStorage.get_default_path",
        lambda cls: mock_sources_path
    )


@pytest.fixture
def temp_db_engine():
    """Provides a fresh isolated DatabaseEngine running PostgreSQL on schema_synapse_test with clean tables."""
    from src.database.db_engine import DatabaseEngine

    custom_cfg = {
        "db_type": "postgres",
        "schema": "schema_synapse_test",
        "db_schema": "schema_synapse_test",
    }
    engine = DatabaseEngine(custom_config=custom_cfg, auto_init=True)

    # Clean tables in test schema for complete test isolation
    conn = engine.get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute("""
                DO $$ 
                DECLARE 
                    r RECORD;
                BEGIN 
                    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'schema_synapse_test') LOOP 
                        EXECUTE 'TRUNCATE TABLE schema_synapse_test.' || quote_ident(r.tablename) || ' RESTART IDENTITY CASCADE;'; 
                    END LOOP; 
                END $$;
            """)
            conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
        finally:
            conn.close()

    return engine


