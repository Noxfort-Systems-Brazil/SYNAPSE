# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
PostgreSQL Database User Repository (SOLID: SRP & DIP).
Handles persistent storage of user credentials in the synapse_users table.
"""

from typing import Dict, Any
from src.security.interfaces import IUserRepository
from src.utils.logging_setup import get_logger


class PostgresUserRepository(IUserRepository):
    """PostgreSQL database persistence for user credentials."""

    def __init__(self, db_engine: Any):
        self.logger = get_logger("PostgresUserRepository")
        self.db_engine = db_engine

    def is_available(self) -> bool:
        """Returns True if the underlying database engine is connected."""
        if not self.db_engine:
            return False
        return bool(getattr(self.db_engine, "is_connected", True))

    def ensure_storage(self) -> None:
        """Ensures the synapse_users table exists in PostgreSQL."""
        if not self.is_available():
            return
        try:
            conn = self.db_engine.get_connection()
            if not conn:
                return
            try:
                cur = conn.cursor()
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS synapse_users (
                        username VARCHAR(128) PRIMARY KEY,
                        password_hash TEXT NOT NULL,
                        role VARCHAR(32) NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        updated_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """)
                conn.commit()
            finally:
                conn.close()
        except Exception as e:
            self.logger.debug(f"[DB USER] Table check notice in PostgresUserRepository: {e}")

    def fetch_users(self) -> Dict[str, Dict[str, str]]:
        """Loads all registered users from synapse_users table."""
        if not self.is_available():
            return {}
        try:
            conn = self.db_engine.get_connection()
            if not conn:
                return {}
            try:
                cur = conn.cursor()
                cur.execute("SELECT username, password_hash, role FROM synapse_users;")
                rows = cur.fetchall()
                result = {}
                for row in rows:
                    result[row[0]] = {"hash": row[1], "role": row[2]}
                return result
            finally:
                conn.close()
        except Exception as e:
            self.logger.debug(f"[DB USER] Failed to fetch users from database: {e}")
            return {}

    def save_user(self, username: str, password_hash: str, role: str) -> bool:
        """Persists or updates a user credential record in PostgreSQL."""
        if not self.is_available():
            return False
        try:
            conn = self.db_engine.get_connection()
            if not conn:
                return False
            try:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO synapse_users (username, password_hash, role, updated_at)
                    VALUES (%s, %s, %s, NOW())
                    ON CONFLICT (username) DO UPDATE
                    SET password_hash = EXCLUDED.password_hash,
                        role = EXCLUDED.role,
                        updated_at = NOW();
                """, (username, password_hash, role))
                conn.commit()
                return True
            finally:
                conn.close()
        except Exception as e:
            self.logger.debug(f"[DB USER] Failed to save user '{username}' to database: {e}")
            return False

    def delete_user(self, username: str) -> bool:
        """Deletes a user record from PostgreSQL."""
        if not self.is_available():
            return False
        try:
            conn = self.db_engine.get_connection()
            if not conn:
                return False
            try:
                cur = conn.cursor()
                cur.execute("DELETE FROM synapse_users WHERE username = %s;", (username,))
                conn.commit()
                return True
            finally:
                conn.close()
        except Exception as e:
            self.logger.debug(f"[DB USER] Failed to delete user '{username}' from database: {e}")
            return False
