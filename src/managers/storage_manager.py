# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: src/managers/storage_manager.py
# Author: Gabriel Moraes
# Date: 2026-02-16

import os
import logging
from pathlib import Path
from typing import Optional, Any, Dict

from src.storage.path_scaffolder import PathScaffolder
from src.storage.vault_sync_service import VaultSyncService
from src.storage.checkpoint_store import CheckpointStore

logger = logging.getLogger("Synapse.StorageManager")


class StorageManager:
    """
    Central Persistence Facade for SYNAPSE.
    Adheres strictly to SOLID by delegating to specialized services:
    - PathScaffolder: OS paths and folder scaffolding.
    - VaultSyncService: Dual-layer cloud vault syncing and disaster recovery.
    - CheckpointStore: Node checkpoint serialization and retrieval.
    """

    def __init__(
        self,
        engine: Optional[Any] = None,
        auto_restore: bool = True,
        project_root: Optional[str] = None
    ):
        self.scaffolder = PathScaffolder(project_root)
        self.home = self.scaffolder.home
        self.documents_dir = self.scaffolder.documents_dir
        self.project_root = self.scaffolder.project_root
        self.checkpoint_dir = self.scaffolder.checkpoint_dir
        self.datalake_dir = self.scaffolder.datalake_dir
        self.base_dir = self.scaffolder.base_dir
        self.golden_dir = self.scaffolder.golden_dir
        self.config_dir = self.scaffolder.config_dir
        self.data_config_dir = self.scaffolder.data_config_dir

        self.engine = engine
        if self.engine is None and project_root is None:
            try:
                from src.database.db_engine import DatabaseEngine
                self.engine = DatabaseEngine()
            except Exception as e:
                logger.debug(f"[StorageManager] Could not auto-initialize DatabaseEngine: {e}")
                self.engine = None

        self.vault_sync = VaultSyncService(self.project_root, self.engine)
        self.cloud_vault = self.vault_sync.cloud_vault
        self.checkpoint_store = CheckpointStore(self.checkpoint_dir, self.vault_sync)
        self.is_connected = True

        self._ensure_structure(auto_restore=auto_restore)
        logger.info(f"[StorageManager] Storage initialized at: {self.project_root}")

    def _ensure_structure(self, auto_restore: bool = True):
        self.scaffolder.ensure_structure()
        if auto_restore:
            self.vault_sync.trigger_disaster_recovery_if_needed()

    def disconnect_database(self) -> None:
        disconnect_fn = getattr(self.engine, "disconnect", None) if self.engine else None
        if callable(disconnect_fn):
            disconnect_fn()
        self.vault_sync = VaultSyncService(self.project_root, None)
        self.cloud_vault = None
        self.is_connected = False
        logger.info("[StorageManager] Database connection closed and cloud vault detached.")

    def connect_database(self, custom_config: Optional[Dict[str, Any]] = None) -> None:
        connect_fn = getattr(self.engine, "connect", None) if self.engine else None
        if callable(connect_fn):
            connect_fn(custom_config)
        elif custom_config:
            from src.database.db_engine import DatabaseEngine
            self.engine = DatabaseEngine(custom_config=custom_config)
        self.vault_sync = VaultSyncService(self.project_root, self.engine)
        self.cloud_vault = self.vault_sync.cloud_vault
        self.checkpoint_store = CheckpointStore(self.checkpoint_dir, self.vault_sync)
        self.is_connected = True
        logger.info("[StorageManager] Database reconnected and cloud vault attached.")

    def sync_file_to_vault(self, filepath: str) -> bool:
        return self.vault_sync.sync_file_to_vault(filepath)

    def restore_file_from_vault(self, relative_path: str, target_filepath: str) -> bool:
        return self.vault_sync.restore_file_from_vault(relative_path, target_filepath)

    def sync_all_to_vault(self) -> None:
        self.vault_sync.sync_all_to_vault()

    def restore_all_from_vault(self) -> int:
        return self.vault_sync.restore_all_from_vault()

    def get_datalake_base_path(self) -> str:
        return self.scaffolder.get_datalake_base_path()

    def get_datalake_golden_path(self) -> str:
        return self.scaffolder.get_datalake_golden_path()

    def get_checkpoint_path(self) -> str:
        return self.scaffolder.get_checkpoint_path()

    def get_checkpoints_path(self) -> str:
        return self.get_checkpoint_path()

    def get_config_path(self) -> str:
        return self.scaffolder.get_config_path()

    def save_node_checkpoint(self, source_id: str, state: Dict[str, Any]) -> bool:
        return self.checkpoint_store.save_node_checkpoint(source_id, state)

    def load_node_checkpoint(self, source_id: str) -> Optional[Dict[str, Any]]:
        return self.checkpoint_store.load_node_checkpoint(source_id)

    def has_phase0_artifacts(self) -> bool:
        try:
            checkpoint_file = Path(self.get_checkpoint_path()) / "best_hparams.pth"
            if not checkpoint_file.exists():
                self.restore_file_from_vault("Checkpoint/best_hparams.pth", str(checkpoint_file))
            return checkpoint_file.exists() and checkpoint_file.stat().st_size > 0
        except Exception as e:
            logger.warning(f"[StorageManager] Error checking Phase 0 artifacts: {e}")
            return False

    def has_phase1_artifacts(self) -> bool:
        try:
            base_dir = Path(self.get_datalake_base_path())
            golden_dir = Path(self.get_datalake_golden_path())
            config_dir = Path(self.get_config_path())

            peak_schedule = config_dir / "peak_schedule.json"
            auditor_checkpoint = config_dir / "auditor_calibrated.pth"
            linguist_checkpoint = config_dir / "linguist_calibrated.json"

            if not peak_schedule.exists():
                self.restore_file_from_vault("data/config/peak_schedule.json", str(peak_schedule))
            if not auditor_checkpoint.exists():
                self.restore_file_from_vault("data/config/auditor_calibrated.pth", str(auditor_checkpoint))
            if not linguist_checkpoint.exists():
                self.restore_file_from_vault("data/config/linguist_calibrated.json", str(linguist_checkpoint))

            base_parquets = list(base_dir.glob("*.parquet")) if base_dir.exists() else []
            if len(base_parquets) == 0 and base_dir.exists():
                base_target = base_dir / "base_v1.parquet"
                if self.restore_file_from_vault("datalake/base/base_v1.parquet", str(base_target)):
                    base_parquets = [base_target]

            golden_parquets = list(golden_dir.glob("*.parquet")) if golden_dir.exists() else []
            if len(golden_parquets) == 0 and golden_dir.exists():
                golden_target = golden_dir / "golden_v1.parquet"
                if self.restore_file_from_vault("datalake/golden/golden_v1.parquet", str(golden_target)):
                    golden_parquets = [golden_target]

            if not base_dir.exists() or not golden_dir.exists() or not config_dir.exists():
                return False

            return (
                len(base_parquets) > 0
                and len(golden_parquets) > 0
                and peak_schedule.exists() and peak_schedule.stat().st_size > 0
                and auditor_checkpoint.exists() and auditor_checkpoint.stat().st_size > 0
                and linguist_checkpoint.exists() and linguist_checkpoint.stat().st_size > 0
            )
        except Exception as e:
            logger.warning(f"[StorageManager] Error checking Phase 1 artifacts: {e}")
            return False

    def has_historical_dataset(self) -> bool:
        try:
            base_dir = Path(self.get_datalake_base_path())
            if base_dir.exists():
                parquets = [p for p in base_dir.glob("*.parquet") if p.stat().st_size > 0]
                if parquets:
                    return True
                target = base_dir / "base_v1.parquet"
                if self.restore_file_from_vault("datalake/base/base_v1.parquet", str(target)):
                    if target.exists() and target.stat().st_size > 0:
                        return True
            golden_dir = Path(self.get_datalake_golden_path())
            if golden_dir.exists():
                goldens = [p for p in golden_dir.glob("*.parquet") if p.stat().st_size > 0]
                if goldens:
                    return True
            return False
        except Exception as e:
            logger.warning(f"[StorageManager] Error checking historical dataset: {e}")
            return False

    def connect(self):
        self.scaffolder.ensure_structure()

    def save_state(self, app_state: Any, file_path: str) -> bool:
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            from src.infrastructure.json_source_storage import JsonSourceStorage
            storage_helper = JsonSourceStorage(file_path, engine=self.engine)
            data_sources = {s.id: s for s in app_state.get_all_data_sources()}
            sources_repo = getattr(app_state, "sources", None)
            associations = getattr(sources_repo, "_associations", {}) if sources_repo is not None else {}
            map_path = app_state.get_map_source_path()
            saved = storage_helper.save(data_sources, associations, map_path)
            self.sync_file_to_vault(file_path)
            return saved
        except Exception as e:
            logger.error(f"[StorageManager] Failed to save state to {file_path}: {e}")
            return False

    def load_state(self, app_state: Any, file_path: str) -> bool:
        try:
            if not os.path.exists(file_path):
                rel_path = os.path.relpath(file_path, str(self.project_root))
                self.restore_file_from_vault(rel_path, file_path)

            if not os.path.exists(file_path):
                return False

            from src.infrastructure.json_source_storage import JsonSourceStorage
            storage_helper = JsonSourceStorage(file_path, engine=self.engine)
            sources, associations, map_path = storage_helper.load()

            sources_repo = getattr(app_state, "sources", None)
            if sources_repo is not None:
                sources_repo._data_sources.clear()
                sources_repo._data_sources.update(sources)
                sources_repo._associations.clear()
                sources_repo._associations.update(associations)
            if map_path:
                app_state.set_map_source_path(map_path)
            return True
        except Exception as e:
            logger.error(f"[StorageManager] Failed to load state from {file_path}: {e}")
            return False

    def close(self):
        pass
