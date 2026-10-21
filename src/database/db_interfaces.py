# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Any, Optional, Dict, Protocol, runtime_checkable


@runtime_checkable
class IConnectionProvider(Protocol):
    """Abstract protocol for database connection providers."""

    @property
    def db_type(self) -> str:
        """Returns the database dialect/type ('postgres')."""
        ...

    @property
    def is_connected(self) -> bool:
        """Returns whether the connector is currently active and allowed to connect."""
        ...

    def get_connection(self) -> Optional[Any]:
        """Provides an active database connection or None on failure."""
        ...

    def reset_circuit_breaker(self) -> None:
        """Resets fatal error flags allowing retry attempts."""
        ...

    def close(self) -> None:
        """Closes all underlying connections or connection pools."""
        ...

    def disconnect(self) -> None:
        """Disconnects and disables active connections and pools."""
        ...

    def connect(self) -> None:
        """Enables database connections."""
        ...


@runtime_checkable
class ISettingsManager(Protocol):
    """Abstract protocol for database and telemetry settings persistence."""

    def load_database_settings(self) -> Dict[str, Any]:
        """Loads database configuration dictionary."""
        ...

    def save_database_settings(self, config_dict: Dict[str, Any]) -> None:
        """Persists updated database configuration."""
        ...

    def load_telemetry_settings(self) -> Dict[str, Any]:
        """Loads telemetry configuration dictionary."""
        ...

    def save_telemetry_settings(self, ip: str, host: str, port: int, connected: bool) -> None:
        """Persists telemetry configuration."""
        ...


@runtime_checkable
class ISchemaMigrator(Protocol):
    """Abstract protocol for schema creation, migrations, and indexing."""

    def initialize_schema(self, conn: Any, db_type: str, schema_name: str = "public") -> None:
        """Applies tables, migrations, and indexes to the target connection."""
        ...
