# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Hybrid Composite User Repository (SOLID: SRP, OCP, ISP & DIP).
Synchronizes local cache with central database providing offline resilience.
"""

from typing import Dict, Optional
from src.security.interfaces import IUserRepository, ISynchronizable
from src.utils.logging_setup import get_logger


class HybridUserRepository(IUserRepository, ISynchronizable):
    """
    Composite Repository: coordinates local cache and remote database storage.
    Depends exclusively on IUserRepository abstractions (DIP).
    """

    def __init__(
        self,
        local_repo: IUserRepository,
        remote_repo: Optional[IUserRepository] = None,
    ):
        self.logger = get_logger("HybridUserRepository")
        self.local_repo = local_repo
        self.remote_repo = remote_repo

    def _is_remote_available(self) -> bool:
        if not self.remote_repo:
            return False
        avail_fn = getattr(self.remote_repo, "is_available", None)
        if callable(avail_fn):
            return bool(avail_fn())
        return True

    def ensure_storage(self) -> None:
        """Ensures local storage and remote database table exist, then triggers sync."""
        self.local_repo.ensure_storage()
        if self._is_remote_available() and self.remote_repo:
            self.remote_repo.ensure_storage()
            self.sync()

    def sync(self) -> None:
        """
        Reconciles users between local cache and central database:
        - Restores users from DB to local file if missing locally.
        - Pushes users created locally while offline up to central DB.
        """
        if not self._is_remote_available() or not self.remote_repo:
            return

        self.remote_repo.ensure_storage()
        db_users = self.remote_repo.fetch_users()
        local_users = self.local_repo.fetch_users()

        modified_local = False
        for uname, udata in db_users.items():
            if uname not in local_users:
                self.local_repo.save_user(uname, udata["hash"], udata["role"])
                modified_local = True

        for uname, udata in local_users.items():
            if uname not in db_users:
                self.remote_repo.save_user(uname, udata.get("hash", ""), udata.get("role", "OPERATOR"))

        if modified_local:
            self.logger.info(
                f"Restored {len(db_users)} user(s) from central database to local security file."
            )

    def fetch_users(self) -> Dict[str, Dict[str, str]]:
        """Returns users from local cache."""
        return self.local_repo.fetch_users()

    def save_user(self, username: str, password_hash: str, role: str) -> bool:
        """Saves user locally and attempts remote sync."""
        local_saved = self.local_repo.save_user(username, password_hash, role)
        if self._is_remote_available() and self.remote_repo:
            self.remote_repo.save_user(username, password_hash, role)
        return local_saved

    def delete_user(self, username: str) -> bool:
        """Deletes user from both local cache and remote database."""
        local_deleted = self.local_repo.delete_user(username)
        remote_deleted = False
        if self._is_remote_available() and self.remote_repo:
            remote_deleted = self.remote_repo.delete_user(username)
        return local_deleted or remote_deleted
