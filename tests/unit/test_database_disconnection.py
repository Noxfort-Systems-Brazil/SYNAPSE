# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import shutil
import tempfile
import pytest

from src.database.db_connectors import PostgresConnector, create_connector
from src.database.db_engine import DatabaseEngine
from src.database.db_settings_manager import DatabaseSettingsManager
from src.managers.storage_manager import StorageManager
from src.infrastructure.json_source_storage import JsonSourceStorage
from src.domain.entities import DataSource, SourceType, SourceStatus


def test_postgres_connector_disconnected_mode():
    """Verifies that PostgresConnector respects connected=False and returns None on get_connection."""
    connector = PostgresConnector(connected=False)
    assert connector.is_connected is False
    assert connector.get_connection() is None

    # Connect
    connector.connect()
    assert connector.is_connected is True

    # Disconnect
    connector.disconnect()
    assert connector.is_connected is False
    assert connector.get_connection() is None


def test_create_connector_respects_settings_ini():
    """Verifies that create_connector honors connected=false from settings manager."""
    with tempfile.NamedTemporaryFile(suffix=".ini", delete=False) as tf:
        temp_ini = tf.name

    try:
        mgr = DatabaseSettingsManager(settings_path=temp_ini)
        mgr.save_database_settings({"connected": "false", "db_type": "postgres"})

        connector = create_connector(settings_mgr=mgr)
        assert connector.is_connected is False
        assert connector.get_connection() is None
    finally:
        if os.path.exists(temp_ini):
            os.unlink(temp_ini)


def test_database_engine_disconnect_and_reconnect():
    """Tests DatabaseEngine disconnect and connect flows."""
    with tempfile.NamedTemporaryFile(suffix=".ini", delete=False) as tf:
        temp_ini = tf.name

    try:
        settings_mgr = DatabaseSettingsManager(settings_path=temp_ini)
        settings_mgr.save_database_settings({
            "db_type": "postgres",
            "schema": "schema_synapse_test",
            "connected": "false"
        })

        engine = DatabaseEngine(
            custom_config={"connected": False, "schema": "schema_synapse_test"},
            settings_manager=settings_mgr,
            auto_init=True
        )

        assert engine.is_connected is False
        assert engine.get_connection() is None

        # Reconnect
        engine.connect({"schema": "schema_synapse_test", "connected": "true"})
        assert engine.is_connected is True

        # Disconnect again
        engine.disconnect()
        assert engine.is_connected is False
        assert engine.get_connection() is None

        loaded = settings_mgr.load_database_settings()
        assert loaded["connected"] is False
    finally:
        if os.path.exists(temp_ini):
            os.unlink(temp_ini)


def test_storage_manager_and_json_source_storage_no_resurrection_when_disconnected():
    """
    CRITICAL TEST: Verifies that when disconnected from the database, StorageManager
    and JsonSourceStorage do NOT resurrect old map or files from the PostgreSQL cloud vault.
    """
    work_dir = tempfile.mkdtemp(prefix="synapse_disc_test_")
    project_root = os.path.join(work_dir, "Synapse")

    try:
        # 1. Create a connected engine for the test schema and save a map to the cloud vault
        connected_engine = DatabaseEngine(
            custom_config={"db_type": "postgres", "schema": "schema_synapse_test", "connected": True},
            auto_init=True
        )

        sources_path = os.path.join(project_root, "config", "sources.json")
        jss_connected = JsonSourceStorage(file_path=sources_path, engine=connected_engine)
        src = DataSource(id="s1", name="Sensor 1", source_type=SourceType.MQTT, connection_string="x")
        jss_connected.save(data_sources={"s1": src}, associations={}, map_path="/maps/old_map.osm")

        # 2. Simulate user disconnecting from DB and deleting local Synapse folder
        shutil.rmtree(project_root)
        assert not os.path.exists(project_root)

        disconnected_engine = DatabaseEngine(
            custom_config={"db_type": "postgres", "schema": "schema_synapse_test", "connected": False},
            auto_init=False
        )
        assert disconnected_engine.is_connected is False

        # 3. StorageManager instantiated while disconnected should NOT restore anything
        sm_disc = StorageManager(engine=disconnected_engine, auto_restore=True, project_root=project_root)
        assert sm_disc.cloud_vault is None

        # 4. JsonSourceStorage instantiated while disconnected should NOT restore old map
        jss_disc = JsonSourceStorage(file_path=sources_path, engine=disconnected_engine)
        loaded_sources, loaded_assoc, loaded_map = jss_disc.load()

        assert loaded_map is None
        assert len(loaded_sources) == 0
        assert not os.path.exists(sources_path)

    finally:
        if os.path.exists(work_dir):
            shutil.rmtree(work_dir)
