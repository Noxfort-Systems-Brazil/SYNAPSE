# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import logging
import threading
from pathlib import Path
from typing import Any, Optional, Dict
from src.database.db_interfaces import IConnectionProvider, ISettingsManager
from src.database.connection_pool_proxy import PooledConnectionProxy

logger = logging.getLogger("Synapse.DatabaseConnectors")


class PostgresConnector(IConnectionProvider):
    """
    Dedicated connection provider for PostgreSQL with built-in ThreadedConnectionPool.
    Encapsulates connection parameters, connection pooling, psycopg2 driver execution,
    search_path schema binding, and fatal error circuit breaking.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        user: str = "user_synapse",
        password: str = "",
        dbname: str = "synapse_db",
        schema: str = "schema_synapse",
        connect_timeout: int = 5,
        min_connections: int = 1,
        max_connections: int = 20,
        enable_pool: bool = True,
        connected: bool = True
    ):
        self.host = host
        self.port = int(port)
        self.user = user
        self.password = password
        self.dbname = dbname
        self.schema = schema

        # Fallback to local settings.ini or env vars if credentials are not explicitly passed
        if not self.password or self.dbname == "synapse_db":
            try:
                from src.database.db_settings_manager import DatabaseSettingsManager
                ini_cfg = DatabaseSettingsManager().load_database_settings()
                if not self.password:
                    self.password = os.getenv("SYNAPSE_DB_PASSWORD") or ini_cfg.get("password", "")
                if self.dbname == "synapse_db":
                    self.dbname = os.getenv("SYNAPSE_DB_NAME") or ini_cfg.get("dbname", self.dbname)
                if self.user == "user_synapse":
                    self.user = os.getenv("SYNAPSE_DB_USER") or ini_cfg.get("user", self.user)
            except Exception:
                pass

        self.connect_timeout = connect_timeout
        self.min_connections = int(min_connections)
        self.max_connections = int(max_connections)
        self.enable_pool = enable_pool
        self._connected = bool(connected)
        self._fatal_db_error = False
        self._pool: Optional[Any] = None
        self._pool_lock = threading.Lock()

    @property
    def db_type(self) -> str:
        return "postgres"

    @property
    def is_connected(self) -> bool:
        return self._connected

    @is_connected.setter
    def is_connected(self, value: bool) -> None:
        self._connected = bool(value)

    def _get_or_create_pool(self) -> Optional[Any]:
        if not self.is_connected or not self.enable_pool or self._fatal_db_error:
            return None

        if self._pool is not None:
            return self._pool

        with self._pool_lock:
            if self._pool is not None:
                return self._pool
            try:
                from psycopg2.pool import ThreadedConnectionPool
                self._pool = ThreadedConnectionPool(
                    minconn=self.min_connections,
                    maxconn=self.max_connections,
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    dbname=self.dbname,
                    options=f"-c search_path={self.schema},public",
                    connect_timeout=self.connect_timeout
                )
                logger.info(
                    f"[POSTGRES_CONNECTOR] ThreadedConnectionPool initialized "
                    f"(min={self.min_connections}, max={self.max_connections}) schema='{self.schema}'."
                )
                return self._pool
            except Exception as e:
                error_msg = str(e).lower()
                if "password authentication failed" in error_msg or "fatal:" in error_msg or "fe_sendauth" in error_msg:
                    self._fatal_db_error = True
                    logger.critical(f"[POSTGRES_CONNECTOR] Fatal PostgreSQL connection error for user '{self.user}' / db '{self.dbname}': {e}")
                else:
                    logger.warning(f"[POSTGRES_CONNECTOR] Could not create connection pool: {e} (will fallback to direct connect)")
                return None

    def get_connection(self) -> Optional[Any]:
        if not self.is_connected or self._fatal_db_error:
            return None

        # 1. Attempt connection via pool
        pool = self._get_or_create_pool()
        if pool:
            try:
                raw_conn = pool.getconn()
                if getattr(raw_conn, "closed", 0) == 0:
                    return PooledConnectionProxy(pool, raw_conn)
                else:
                    pool.putconn(raw_conn, close=True)
            except Exception as pe:
                logger.debug(f"[POSTGRES_CONNECTOR] Pool getconn notice: {pe}, attempting direct connection.")

        # 2. Fallback to direct connection if pool is disabled, exhausted, or failed
        try:
            import psycopg2
            return psycopg2.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                dbname=self.dbname,
                options=f"-c search_path={self.schema},public",
                connect_timeout=self.connect_timeout
            )
        except Exception as e:
            error_msg = str(e).lower()
            if "password authentication failed" in error_msg or "fatal:" in error_msg or "fe_sendauth" in error_msg:
                self._fatal_db_error = True
                logger.critical(f"[POSTGRES_CONNECTOR] Fatal PostgreSQL connection error for user '{self.user}' / db '{self.dbname}': {e}")
            else:
                logger.error(f"[POSTGRES_CONNECTOR] Failed to connect to PostgreSQL: {e}")
            return None

    def reset_circuit_breaker(self) -> None:
        self._fatal_db_error = False
        self.close()

    def disconnect(self) -> None:
        """Disconnects and releases all connection resources."""
        self.is_connected = False
        self.close()

    def connect(self) -> None:
        """Enables connection attempts and resets error states."""
        self.is_connected = True
        self.reset_circuit_breaker()

    def close(self) -> None:
        """Closes all connections in the pool."""
        with self._pool_lock:
            if self._pool is not None:
                try:
                    self._pool.closeall()
                    logger.info("[POSTGRES_CONNECTOR] ThreadedConnectionPool closed successfully.")
                except Exception as e:
                    logger.warning(f"[POSTGRES_CONNECTOR] Error closing connection pool: {e}")
                finally:
                    self._pool = None


def create_connector(
    custom_config: Optional[Dict[str, Any]] = None,
    settings_mgr: Optional[ISettingsManager] = None,
    db_name: str = "synapse_db"
) -> IConnectionProvider:
    """
    Factory function producing the appropriate IConnectionProvider implementation.
    Synapse strictly uses PostgreSQL; SQLite is not supported.
    """
    custom = custom_config or {}
    ini_db = settings_mgr.load_database_settings() if settings_mgr else {}

    db_type = (
        custom.get("db_type")
        or os.getenv("SYNAPSE_DB_TYPE")
        or ini_db.get("db_type")
        or "postgres"
    ).lower()

    if db_type == "sqlite":
        raise ValueError("Synapse opera estritamente com PostgreSQL. Suporte ao SQLite foi descontinuado.")

    host = custom.get("host") or custom.get("db_host") or os.getenv("SYNAPSE_DB_HOST") or ini_db.get("host", "localhost")
    port = int(custom.get("port") or custom.get("db_port") or os.getenv("SYNAPSE_DB_PORT") or ini_db.get("port", 5432))
    user = custom.get("user") or custom.get("db_user") or os.getenv("SYNAPSE_DB_USER") or ini_db.get("user", "user_synapse")
    password = custom.get("password") or custom.get("db_password") or os.getenv("SYNAPSE_DB_PASSWORD") or ini_db.get("password", "")
    dbname = custom.get("dbname") or custom.get("db_name") or os.getenv("SYNAPSE_DB_NAME") or ini_db.get("dbname", "synapse_db")
    schema = custom.get("schema") or custom.get("db_schema") or os.getenv("SYNAPSE_DB_SCHEMA") or ini_db.get("schema", "schema_synapse")

    min_conn = int(custom.get("min_connections") or os.getenv("SYNAPSE_DB_POOL_MIN") or 1)
    max_conn = int(custom.get("max_connections") or os.getenv("SYNAPSE_DB_POOL_MAX") or 20)
    enable_pool = custom.get("enable_pool", True)
    if isinstance(enable_pool, str):
        enable_pool = enable_pool.lower() not in ("false", "0", "no")

    connected_setting = custom.get("connected")
    if connected_setting is not None:
        if isinstance(connected_setting, str):
            is_connected = connected_setting.lower() in ("true", "1", "yes")
        else:
            is_connected = bool(connected_setting)
    elif custom_config:
        is_connected = True
    else:
        is_connected = ini_db.get("connected", False)

    return PostgresConnector(
        host=host,
        port=port,
        user=user,
        password=password,
        dbname=dbname,
        schema=schema,
        min_connections=min_conn,
        max_connections=max_conn,
        enable_pool=enable_pool,
        connected=is_connected
    )

