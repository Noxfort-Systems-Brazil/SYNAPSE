# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import logging
from typing import Any, Optional, Dict

from src.database.db_interfaces import IConnectionProvider, ISettingsManager, ISchemaMigrator
from src.database.db_settings_manager import DatabaseSettingsManager
from src.database.db_connectors import create_connector, PostgresConnector
from src.database.db_migrator import DatabaseMigrator

logger = logging.getLogger("Synapse.DatabaseEngine")


class DatabaseEngine:
    """
    Central facade and orchestrator for the Synapse Database Layer.
    Adheres to SOLID principles:
    - Single Responsibility (SRP): Delegates connection logic, settings I/O, and DDL migrations.
    - Open/Closed (OCP): Works with any IConnectionProvider or ISchemaMigrator implementation.
    - Dependency Inversion (DIP): Depends on abstract contracts and supports dependency injection.
    """

    def __init__(
        self,
        db_name: str = "synapse_db",
        custom_config: Optional[Dict[str, Any]] = None,
        auto_init: bool = True,
        connector: Optional[IConnectionProvider] = None,
        settings_manager: Optional[ISettingsManager] = None,
        migrator: Optional[ISchemaMigrator] = None
    ):
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        self.settings_path = os.path.join(self.project_root, "config", "settings.ini")

        # 1. Injected or default settings manager
        self.settings_manager = settings_manager or DatabaseSettingsManager(settings_path=self.settings_path)

        # 2. Injected or factory-created connection provider
        self.connector = connector or create_connector(
            custom_config=custom_config,
            settings_mgr=self.settings_manager,
            db_name=db_name
        )

        # 3. Injected or default schema migrator
        self.migrator = migrator or DatabaseMigrator()

        if auto_init:
            self._initialize_db()
            logger.info(f"[DB_ENGINE] Central Engine Initialized. DB: {self.db_type}")

    @property
    def db_type(self) -> str:
        """Returns current database dialect ('postgres')."""
        return self.connector.db_type

    @property
    def db_path(self) -> str:
        """Deprecated SQLite path property; always empty in PostgreSQL."""
        return ""

    @db_path.setter
    def db_path(self, value: str) -> None:
        """Deprecated SQLite path setter (no-op)."""
        pass

    @property
    def db_name_pg(self) -> str:
        return getattr(self.connector, "dbname", "")

    @property
    def db_schema(self) -> str:
        return getattr(self.connector, "schema", "public")

    @property
    def _fatal_db_error(self) -> bool:
        return getattr(self.connector, "_fatal_db_error", False)

    @_fatal_db_error.setter
    def _fatal_db_error(self, value: bool) -> None:
        if getattr(self.connector, "_fatal_db_error", None) is not None:
            setattr(self.connector, "_fatal_db_error", value)

    @property
    def is_connected(self) -> bool:
        """Indicates whether the database connector is currently active and allowed to connect."""
        return getattr(self.connector, "is_connected", True)

    def get_connection(self) -> Optional[Any]:
        """Provides an active database connection via the configured connector."""
        if not self.is_connected:
            return None
        return self.connector.get_connection()

    def reset_circuit_breaker(self) -> None:
        """Resets the fatal error circuit breaker on the connector."""
        self.connector.reset_circuit_breaker()

    def disconnect(self) -> None:
        """Disconnects from the database, closes pools, and persists connected=false."""
        disc_fn = getattr(self.connector, "disconnect", None) or getattr(self.connector, "close", None)
        if callable(disc_fn):
            disc_fn()
        self.save_settings_to_ini({"connected": "false"})
        logger.info("[DB_ENGINE] Database disconnected and connected=false persisted.")

    def connect(self, config_dict: Optional[Dict[str, Any]] = None) -> bool:
        """Enables database connectivity, updates settings, and initializes schema."""
        if config_dict:
            self.save_settings_to_ini(config_dict)
        conn_fn = getattr(self.connector, "connect", None)
        if callable(conn_fn):
            conn_fn()
        self.save_settings_to_ini({"connected": "true"})
        self._initialize_db()
        logger.info("[DB_ENGINE] Database connected and schema synchronized.")
        return self.is_connected

    def close(self) -> None:
        """Closes all connections and releases connection pool resources."""
        close_fn = getattr(self.connector, "close", None)
        if callable(close_fn):
            close_fn()

    def load_database_settings(self) -> Dict[str, Any]:
        """Delegates database settings retrieval to the settings manager."""
        return self.settings_manager.load_database_settings()

    def save_settings_to_ini(self, config_dict: Dict[str, Any]) -> None:
        """Delegates connection settings persistence to the settings manager."""
        self.settings_manager.save_database_settings(config_dict)

    def load_telemetry_settings(self) -> Dict[str, Any]:
        """Delegates telemetry settings retrieval to the settings manager."""
        return self.settings_manager.load_telemetry_settings()

    def save_telemetry_settings(self, ip: str, host: str, port: int, connected: bool) -> None:
        """Delegates telemetry settings persistence to the settings manager."""
        self.settings_manager.save_telemetry_settings(ip, host, port, connected)

    def _load_schema_config(self) -> Dict[str, Any]:
        """Helper to expose schema configuration for test inspection or monkeypatching."""
        load_fn = getattr(self.migrator, "_load_schema_config", None)
        return load_fn() if callable(load_fn) else {}

    def _initialize_db(self) -> None:
        """Executes table creation, column migrations, and index generation."""
        if not self.is_connected:
            logger.info("[DB_ENGINE] Database is marked as disconnected (connected=false). Skipping schema initialization.")
            return
        conn = self.get_connection()
        if not conn:
            return
        try:
            custom_schema = self._load_schema_config()
            self.migrator.initialize_schema(
                conn=conn,
                db_type=self.db_type,
                schema_name=self.db_schema,
                schema_config=custom_schema
            )
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
