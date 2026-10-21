# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: src/storage/vault_sync_service.py
# Author: Gabriel Moraes
# Date: 2026-09-14

import os
import logging
from pathlib import Path
from typing import Optional, Any

logger = logging.getLogger("Synapse.Storage.VaultSyncService")


class VaultSyncService:
    """
    Encapsulates Cloud Vault sync, file upload/restore, and disaster recovery.
    """

    def __init__(self, project_root: Path, engine: Optional[Any] = None):
        self.project_root = project_root
        self.engine = engine
        self.cloud_vault: Optional[Any] = None
        self._init_vault()

    def _init_vault(self):
        if self.engine and getattr(self.engine, "is_connected", True):
            try:
                from src.repositories.cloud_vault_repo import CloudVaultRepository
                self.cloud_vault = CloudVaultRepository(self.engine)
            except Exception as e:
                logger.debug(f"Could not initialize CloudVaultRepository: {e}")
                self.cloud_vault = None
        else:
            self.cloud_vault = None

    def sync_file_to_vault(self, filepath: str) -> bool:
        """Uploads a local file to the cloud file vault in PostgreSQL."""
        if not self.cloud_vault or not getattr(self.engine, "is_connected", True) or not os.path.exists(filepath):
            return False
        try:
            return self.cloud_vault.sync_file_to_vault(filepath, str(self.project_root))
        except Exception as e:
            logger.debug(f"Failed to sync {filepath} to vault: {e}")
            return False

    def restore_file_from_vault(self, relative_path: str, target_filepath: str) -> bool:
        """Restores a single file from the cloud file vault to disk."""
        if not self.cloud_vault or not getattr(self.engine, "is_connected", True):
            return False
        try:
            return self.cloud_vault.restore_file_from_vault(relative_path, target_filepath)
        except Exception as e:
            logger.debug(f"Failed to restore {relative_path} from vault: {e}")
            return False

    def sync_all_to_vault(self) -> None:
        """Syncs all files in project root to cloud vault."""
        if not self.cloud_vault or not getattr(self.engine, "is_connected", True):
            return
        try:
            self.cloud_vault.sync_all_files_to_vault(str(self.project_root))
        except Exception as e:
            logger.debug(f"Failed to sync all files to vault: {e}")

    def restore_all_from_vault(self) -> int:
        """Restores all files from cloud vault into project root."""
        if not self.cloud_vault or not getattr(self.engine, "is_connected", True):
            return 0
        try:
            return self.cloud_vault.restore_all_files_from_vault(str(self.project_root))
        except Exception as e:
            logger.debug(f"Failed to restore all files from vault: {e}")
            return 0

    def trigger_disaster_recovery_if_needed(self) -> None:
        """Restores files if project directory is empty and vault is online."""
        if not self.cloud_vault or not getattr(self.engine, "is_connected", True):
            return
        try:
            existing_files = [
                f for f in self.project_root.glob("**/*")
                if f.is_file() and not f.name.endswith(".db") and not f.name.endswith(".log")
            ]
            if len(existing_files) == 0:
                restored = self.restore_all_from_vault()
                if restored > 0:
                    logger.info(f"🌟 Disaster recovery: {restored} files restored from cloud vault.")
        except Exception as re:
            logger.debug(f"Vault auto-restore notice: {re}")
