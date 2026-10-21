# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: src/database/connection_pool_proxy.py
# Author: Gabriel Moraes
# Date: 2026-09-14

import logging
from typing import Any

logger = logging.getLogger("Synapse.Database.ConnectionPoolProxy")


class PooledConnectionProxy:
    """
    Transparent proxy for a pooled psycopg2 connection.
    Intercepts .close() to return the connection to ThreadedConnectionPool
    instead of terminating the underlying TCP socket.
    """

    def __init__(self, pool: Any, conn: Any):
        self._pool = pool
        self._conn = conn
        self._returned = False

    @property
    def closed(self) -> int:
        if self._returned:
            return 1
        return getattr(self._conn, "closed", 0)

    @property
    def raw_connection(self) -> Any:
        return self._conn

    def close(self) -> None:
        """Returns connection back to pool cleanly with transaction rollback reset."""
        if not self._returned:
            self._returned = True
            if self._pool and self._conn:
                try:
                    is_broken = getattr(self._conn, "closed", 1) != 0
                    if not is_broken:
                        try:
                            if not getattr(self._conn, "autocommit", False):
                                self._conn.rollback()
                        except Exception:
                            is_broken = True
                    self._pool.putconn(self._conn, close=is_broken)
                except Exception as e:
                    logger.debug(f"[PooledConnectionProxy] Error returning connection to pool: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            try:
                self._conn.rollback()
            except Exception:
                pass
        self.close()

    @property
    def autocommit(self) -> bool:
        return getattr(self._conn, "autocommit", False)

    @autocommit.setter
    def autocommit(self, val: bool) -> None:
        setattr(self._conn, "autocommit", val)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._conn, name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ("_pool", "_conn", "_returned"):
            super().__setattr__(name, value)
        else:
            setattr(self._conn, name, value)
