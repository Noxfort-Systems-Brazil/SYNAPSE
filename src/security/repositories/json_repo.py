# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
JSON File User Repository (SOLID: SRP & DIP).
Handles persistent storage of user credentials in a local security.json file.
"""

import os
import json
from typing import Dict, Any
from src.security.interfaces import IUserRepository
from src.utils.logging_setup import get_logger


class JsonUserRepository(IUserRepository):
    """Local JSON file persistence for user identities."""

    def __init__(self, security_file: str):
        self.logger = get_logger("JsonUserRepository")
        self.security_file = security_file

    def ensure_storage(self) -> None:
        """Ensures the JSON database file exists with initial structure."""
        target_dir = os.path.dirname(self.security_file)
        if target_dir:
            os.makedirs(target_dir, exist_ok=True)
        if not os.path.exists(self.security_file):
            default_db = {"users": {}, "failed_attempts": 0}
            self._save_db(default_db)
            self.logger.info("Security file created with clean user table.")

    def _load_db(self) -> Dict[str, Any]:
        """Loads raw JSON structure from security.json."""
        if not os.path.exists(self.security_file):
            self.ensure_storage()
        try:
            with open(self.security_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error reading security database: {e}")
            return {"users": {}, "failed_attempts": 0}

    def _save_db(self, db: Dict[str, Any]) -> None:
        """Saves raw JSON structure to security.json."""
        try:
            target_dir = os.path.dirname(self.security_file)
            if target_dir:
                os.makedirs(target_dir, exist_ok=True)
            with open(self.security_file, "w", encoding="utf-8") as f:
                json.dump(db, f, indent=4)
        except Exception as e:
            self.logger.error(f"Error saving security database: {e}")

    def fetch_users(self) -> Dict[str, Dict[str, str]]:
        """Loads all registered users from security.json."""
        db = self._load_db()
        return dict(db.get("users", {}))

    def save_user(self, username: str, password_hash: str, role: str) -> bool:
        """Creates or updates a user credential record."""
        db = self._load_db()
        if "users" not in db:
            db["users"] = {}
        db["users"][username] = {"hash": password_hash, "role": role}
        self._save_db(db)
        return True

    def delete_user(self, username: str) -> bool:
        """Deletes a user credential record if present."""
        db = self._load_db()
        users = db.get("users", {})
        if username in users:
            del users[username]
            db["users"] = users
            self._save_db(db)
            return True
        return False
