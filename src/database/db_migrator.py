# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import json
import logging
from typing import Any, Optional, Dict
from src.database.db_interfaces import ISchemaMigrator

logger = logging.getLogger("Synapse.DatabaseMigrator")


class DatabaseMigrator(ISchemaMigrator):
    """
    Dedicated executor for schema definitions, migrations, and index creations.
    Adheres to Single Responsibility Principle (SRP) by decoupling DDL maintenance from connection management.
    """

    def __init__(self, schema_queries_path: Optional[str] = None):
        if schema_queries_path:
            self.schema_queries_path = os.path.abspath(schema_queries_path)
        else:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            self.schema_queries_path = os.path.join(project_root, "config", "synapse_schema_queries.json")

    def _load_schema_config(self) -> Dict[str, Any]:
        """Loads JSON schema definition and migration queries."""
        try:
            if os.path.exists(self.schema_queries_path):
                with open(self.schema_queries_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"[DB_MIGRATOR] Failed to load schema queries from {self.schema_queries_path}: {e}")
        return {}

    def initialize_schema(
        self,
        conn: Any,
        db_type: str,
        schema_name: str = "schema_synapse",
        schema_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Creates tables, executes column migrations, and generates performance indexes.
        Employs strict per-statement rollback on error to preserve PostgreSQL transaction integrity.
        """
        if not conn:
            return

        try:
            cursor = conn.cursor()
            cfg = schema_config if schema_config is not None else self._load_schema_config()
            dialect_config = cfg.get(db_type, cfg.get("postgres", {}))

            # 1. Create Tables
            for table_sql in dialect_config.get("tables", []):
                try:
                    cursor.execute(table_sql)
                    conn.commit()
                except Exception as te:
                    if conn:
                        try:
                            conn.rollback()
                        except Exception:
                            pass
                    logger.debug(f"[DB_MIGRATOR] Table creation notice: {te}")

            # 2. Migrations (PostgreSQL information_schema inspection)
            migrations = dialect_config.get("migrations", [])
            try:
                cursor.execute("""
                    SELECT table_name, column_name FROM information_schema.columns 
                    WHERE table_schema = %s OR table_schema = 'public';
                """, (schema_name,))
                existing_cols = {(row[0], row[1]) for row in cursor.fetchall()}
                conn.commit()
            except Exception:
                if conn:
                    try:
                        conn.rollback()
                    except Exception:
                        pass
                existing_cols = set()

            for m in migrations:
                if isinstance(m, dict):
                    t_name = m.get("table", "synapse_sensor_telemetry_raw")
                    col_name = m.get("column")
                    if (t_name, col_name) not in existing_cols:
                        try:
                            cursor.execute(m["sql"])
                            conn.commit()
                        except Exception as me:
                            if conn:
                                try:
                                    conn.rollback()
                                except Exception:
                                    pass
                            logger.debug(f"[DB_MIGRATOR] Migration notice: {me}")

            # 3. Create Indexes
            for index_sql in dialect_config.get("indexes", []):
                try:
                    cursor.execute(index_sql)
                    conn.commit()
                except Exception as ie:
                    if conn:
                        try:
                            conn.rollback()
                        except Exception:
                            pass
                    logger.debug(f"[DB_MIGRATOR] Index creation notice: {ie}")

            # 4. Storage Optimizations & Tuning
            for opt_sql in dialect_config.get("optimizations", []):
                try:
                    cursor.execute(opt_sql)
                    conn.commit()
                except Exception as oe:
                    if conn:
                        try:
                            conn.rollback()
                        except Exception:
                            pass
                    logger.debug(f"[DB_MIGRATOR] Optimization notice: {oe}")

        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except Exception:
                    pass
            logger.error(f"[DB_MIGRATOR] Error during initialize_schema: {e}")
