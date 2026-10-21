# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: src/storage/checkpoint_store.py
# Author: Gabriel Moraes
# Date: 2026-09-14

import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("Synapse.Storage.CheckpointStore")


class CheckpointStore:
    """
    Handles saving, loading, and recovery of PyTorch node & model state checkpoints.
    """

    def __init__(self, checkpoint_dir: Path, vault_sync: Optional[Any] = None):
        self.checkpoint_dir = checkpoint_dir
        self.vault_sync = vault_sync

    def save_node_checkpoint(self, source_id: str, state: Dict[str, Any]) -> bool:
        """Persists a single node state checkpoint to disk and triggers vault sync."""
        try:
            import torch
            self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
            file_path = self.checkpoint_dir / f"state_{source_id}.pth"
            torch.save(state, str(file_path))
            if self.vault_sync:
                self.vault_sync.sync_file_to_vault(str(file_path))
            return True
        except Exception as e:
            logger.error(f"Failed to save node checkpoint for '{source_id}': {e}")
            return False

    def load_node_checkpoint(self, source_id: str) -> Optional[Dict[str, Any]]:
        """Loads a node state checkpoint (restoring from vault if missing on disk)."""
        try:
            import torch
            file_path = self.checkpoint_dir / f"state_{source_id}.pth"
            if not file_path.exists() and self.vault_sync:
                self.vault_sync.restore_file_from_vault(f"Checkpoint/state_{source_id}.pth", str(file_path))
            if file_path.exists():
                return torch.load(str(file_path), map_location="cpu", weights_only=False)
            return None
        except Exception as e:
            logger.error(f"Failed to load checkpoint for '{source_id}': {e}")
            return None
