# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: src/storage/path_scaffolder.py
# Author: Gabriel Moraes
# Date: 2026-09-14

import os
import logging
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger("Synapse.Storage.PathScaffolder")


class PathScaffolder:
    """
    Handles OS-level folder scaffolding and directory path resolution (SRP).
    Creates and resolves mandatory Synapse storage layout.
    """

    def __init__(self, project_root: Optional[str] = None):
        self.home = Path.home()

        # Resolve Documents directory (XDG / cross-platform / locale)
        xdg_docs = os.environ.get("XDG_DOCUMENTS_DIR")
        if xdg_docs and Path(xdg_docs).exists():
            docs = Path(xdg_docs)
        else:
            docs = self.home / "Documentos"
            if not docs.exists():
                docs = self.home / "Documents"
        self.documents_dir = docs

        env_root = os.environ.get("SYNAPSE_HOME") or os.environ.get("SYNAPSE_DATA_DIR")
        if project_root:
            self.project_root = Path(project_root)
        elif env_root:
            self.project_root = Path(env_root)
        else:
            self.project_root = self.documents_dir / "Synapse"

        # Scaffolding target paths
        self.checkpoint_dir = self.project_root / "Checkpoint"
        self.datalake_dir = self.project_root / "datalake"
        self.base_dir = self.datalake_dir / "base"
        self.golden_dir = self.datalake_dir / "golden"
        self.config_dir = self.project_root / "config"
        self.data_config_dir = self.project_root / "data" / "config"
        self.data_db_dir = self.project_root / "data" / "db"
        self.logs_dir = self.project_root / "logs"

    def get_mandatory_paths(self) -> List[Path]:
        return [
            self.project_root,
            self.checkpoint_dir,
            self.datalake_dir,
            self.base_dir,
            self.golden_dir,
            self.config_dir,
            self.data_config_dir,
            self.data_db_dir,
        ]

    def ensure_structure(self) -> None:
        """Creates mandatory directory structure if missing."""
        for path in self.get_mandatory_paths():
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    logger.critical(f"Failed to create directory {path}: {e}")

    def get_project_root(self) -> str:
        return str(self.project_root)

    def get_datalake_base_path(self) -> str:
        return str(self.base_dir)

    def get_datalake_golden_path(self) -> str:
        return str(self.golden_dir)

    def get_checkpoint_path(self) -> str:
        return str(self.checkpoint_dir)

    def get_config_path(self) -> str:
        return str(self.data_config_dir)

    def get_system_config_path(self) -> str:
        return str(self.config_dir)

    def get_logs_path(self) -> str:
        return str(self.logs_dir)

    def get_config_file(self, filename: str) -> str:
        return str(self.data_config_dir / filename)

    def get_checkpoint_file(self, filename: str) -> str:
        return str(self.checkpoint_dir / filename)

