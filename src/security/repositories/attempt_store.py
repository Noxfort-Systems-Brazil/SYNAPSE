# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Rate-Limiting Attempt Counter Storage (SOLID: SRP & DIP).
Isolates failed attempt tracking from user account persistence.
"""

import os
import json
from typing import Dict, Any
from src.security.interfaces import IAttemptCounterStore


class JsonAttemptStore(IAttemptCounterStore):
    """Persists failed authentication attempts count in a JSON state file."""

    def __init__(self, state_file: str):
        self.state_file = state_file

    def _read_db(self) -> Dict[str, Any]:
        if not os.path.exists(self.state_file):
            return {"users": {}, "failed_attempts": 0}
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"users": {}, "failed_attempts": 0}

    def _write_db(self, db: Dict[str, Any]) -> None:
        target_dir = os.path.dirname(self.state_file)
        if target_dir:
            os.makedirs(target_dir, exist_ok=True)
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(db, f, indent=4)
        except Exception:
            pass

    def get_failed_attempts(self) -> int:
        db = self._read_db()
        return db.get("failed_attempts", 0)

    def set_failed_attempts(self, count: int) -> None:
        db = self._read_db()
        db["failed_attempts"] = count
        self._write_db(db)


class MemoryAttemptStore(IAttemptCounterStore):
    """In-memory attempt store for transient or testing environments."""

    def __init__(self, initial_count: int = 0):
        self._counter = initial_count

    def get_failed_attempts(self) -> int:
        return self._counter

    def set_failed_attempts(self, count: int) -> None:
        self._counter = count
