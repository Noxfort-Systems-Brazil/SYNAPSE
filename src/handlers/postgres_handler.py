# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: src/handlers/postgres_handler.py
# Author: Gabriel Moraes
# Date: 2026-09-14

import threading
from typing import Any, Callable, Optional

from src.ipc.ipc_protocol import IpcMessage
from src.ipc.command_router import Responder


class PostgresCommandHandler:
    """Handles PostgreSQL connection verification, initialization, and telemetry config."""

    def __init__(
        self,
        controller: Any,
        worker_factory: Optional[Callable[[], Any]] = None,
        manager_factory: Optional[Callable[[], Any]] = None,
    ):
        self.controller = controller
        self._worker_factory = worker_factory or self._default_worker_factory
        self._manager_factory = manager_factory or self._default_manager_factory

    @staticmethod
    def _default_worker_factory() -> Any:
        from src.infrastructure.postgres_manager import PostgresWorker
        return PostgresWorker()

    @staticmethod
    def _default_manager_factory() -> Any:
        from src.infrastructure.postgres_manager import PostgresManager
        return PostgresManager()

    def handle_test_db_connection(self, msg: IpcMessage, responder: Responder) -> None:
        config = msg.payload.get("config", {})
        worker = self._worker_factory()
        check_fn = getattr(worker, "do_check_connection", None)
        if callable(check_fn):
            try:
                check_fn(config)
            except Exception:
                pass

        def _run():
            try:
                import psycopg2
                schema = config.get("schema", "schema_synapse")
                conn = psycopg2.connect(
                    host=config.get("host", "localhost"),
                    port=config.get("port", 5432),
                    database=config.get("dbname", "synapse_db"),
                    user=config.get("user", "user_synapse"),
                    password=config.get("password", ""),
                    options=f"-c search_path={schema},public",
                    connect_timeout=3
                )
                conn.close()

                try:
                    from src.database.db_settings_manager import DatabaseSettingsManager
                    pg_cfg = dict(config)
                    pg_cfg["db_type"] = "postgres"
                    pg_cfg["schema"] = schema
                    pg_cfg["connected"] = "true"
                    settings_mgr = DatabaseSettingsManager()
                    settings_mgr.save_database_settings(pg_cfg)

                    storage = getattr(self.controller, "storage", None)
                    conn_db_fn = getattr(storage, "connect_database", None) if storage else None
                    if callable(conn_db_fn):
                        conn_db_fn(pg_cfg)
                except Exception:
                    pass

                responder(True, {"message": f"Conexão bem-sucedida ao schema '{schema}'."})
            except Exception as e:
                msg_err = str(e).split('\n')[0]
                responder(False, error=f"Falha na conexão: {msg_err}")

        threading.Thread(target=_run, daemon=True).start()

    def handle_initialize_db(self, msg: IpcMessage, responder: Responder) -> None:
        root_pass = msg.payload.get("root_password", "")
        config = msg.payload.get("config", {})

        def _run():
            try:
                import psycopg2
                from psycopg2 import sql as pg_sql
                from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT as AUTOCOMMIT

                host = config.get("host", "localhost")
                port = config.get("port", 5432)
                target_user = config.get("user", "user_synapse")
                target_pass = config.get("password", "")
                target_db = config.get("dbname", "synapse_db")
                target_schema = config.get("schema", "schema_synapse")

                # 1. Connect as postgres root
                conn = psycopg2.connect(
                    host=host, port=port, database="postgres",
                    user="postgres", password=root_pass, connect_timeout=5
                )
                conn.set_isolation_level(AUTOCOMMIT)
                cursor = conn.cursor()

                # 2. Create user if not exists
                cursor.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (target_user,))
                if not cursor.fetchone():
                    cursor.execute(
                        pg_sql.SQL("CREATE USER {} WITH ENCRYPTED PASSWORD %s").format(
                            pg_sql.Identifier(target_user)
                        ), (target_pass,)
                    )

                # 3. Create database if not exists
                cursor.execute("SELECT 1 FROM pg_database WHERE datname=%s", (target_db,))
                if not cursor.fetchone():
                    cursor.execute(
                        pg_sql.SQL("CREATE DATABASE {} OWNER {}").format(
                            pg_sql.Identifier(target_db),
                            pg_sql.Identifier(target_user)
                        )
                    )

                cursor.close()
                conn.close()

                # 4. Connect to target DB as root to provision schema
                conn2 = psycopg2.connect(
                    host=host, port=port, database=target_db,
                    user="postgres", password=root_pass, connect_timeout=5
                )
                conn2.set_isolation_level(AUTOCOMMIT)
                cur2 = conn2.cursor()

                cur2.execute(
                    pg_sql.SQL("GRANT ALL PRIVILEGES ON DATABASE {} TO {}").format(
                        pg_sql.Identifier(target_db), pg_sql.Identifier(target_user)
                    )
                )
                cur2.execute(
                    pg_sql.SQL("CREATE SCHEMA IF NOT EXISTS {} AUTHORIZATION {}").format(
                        pg_sql.Identifier(target_schema), pg_sql.Identifier(target_user)
                    )
                )
                cur2.execute(
                    pg_sql.SQL("GRANT ALL ON SCHEMA {} TO {}").format(
                        pg_sql.Identifier(target_schema), pg_sql.Identifier(target_user)
                    )
                )
                cur2.close()
                conn2.close()

                # 5. Initialize tables via DatabaseEngine
                try:
                    from src.database.db_engine import DatabaseEngine
                    pg_cfg = dict(config)
                    pg_cfg["db_type"] = "postgres"
                    pg_cfg["user"] = target_user
                    pg_cfg["password"] = target_pass
                    pg_cfg["dbname"] = target_db
                    pg_cfg["schema"] = target_schema
                    pg_cfg["connected"] = "true"
                    pg_cfg["setup_done"] = "true"
                    engine = DatabaseEngine(custom_config=pg_cfg)
                    engine.save_settings_to_ini(pg_cfg)

                    storage = getattr(self.controller, "storage", None)
                    conn_db_fn = getattr(storage, "connect_database", None) if storage else None
                    if callable(conn_db_fn):
                        conn_db_fn(pg_cfg)
                except Exception:
                    pass

                responder(True, {
                    "message": f"Usuário '{target_user}', schema '{target_schema}' e tabelas criados com sucesso!"
                })
            except Exception as e:
                msg_err = str(e).split('\n')[0]
                responder(False, error=f"Falha na inicialização: {msg_err}")

        threading.Thread(target=_run, daemon=True).start()

    def handle_get_database_config(self, msg: IpcMessage, responder: Responder) -> None:
        try:
            from src.database.db_settings_manager import DatabaseSettingsManager
            settings_mgr = DatabaseSettingsManager()
            cfg = settings_mgr.load_database_settings()
            responder(True, cfg)
        except Exception as e:
            responder(False, error=str(e))

    def handle_disconnect_db(self, msg: IpcMessage, responder: Responder) -> None:
        try:
            from src.database.db_settings_manager import DatabaseSettingsManager
            settings_mgr = DatabaseSettingsManager()
            settings_mgr.save_database_settings({"connected": "false"})

            storage = getattr(self.controller, "storage", None)
            if storage is not None:
                disc_fn = getattr(storage, "disconnect_database", None)
                if callable(disc_fn):
                    disc_fn()
                else:
                    eng = getattr(storage, "engine", None)
                    eng_disc = getattr(eng, "disconnect", None) if eng is not None else None
                    if callable(eng_disc):
                        eng_disc()

            ctrl_eng = getattr(self.controller, "db_engine", None)
            ctrl_disc = getattr(ctrl_eng, "disconnect", None) if ctrl_eng is not None else None
            if callable(ctrl_disc):
                ctrl_disc()

            responder(True, {"message": "Desconectado com sucesso."})
        except Exception as e:
            responder(False, error=str(e))

    def handle_get_telemetry_config(self, msg: IpcMessage, responder: Responder) -> None:
        try:
            from src.database.db_settings_manager import DatabaseSettingsManager
            settings_mgr = DatabaseSettingsManager()
            cfg = settings_mgr.load_telemetry_settings()
            responder(True, cfg)
        except Exception as e:
            responder(False, error=str(e))

    def handle_save_telemetry_config(self, msg: IpcMessage, responder: Responder) -> None:
        try:
            from src.database.db_settings_manager import DatabaseSettingsManager
            settings_mgr = DatabaseSettingsManager()
            payload = msg.payload or {}
            ip = payload.get("ip", "localhost")
            host = payload.get("host", "localhost")
            port = int(payload.get("port", 1883))
            connected = bool(payload.get("connected", False))
            settings_mgr.save_telemetry_settings(ip, host, port, connected)

            telem_svc = getattr(self.controller, "telemetry", None)
            reconf_fn = getattr(telem_svc, "reconfigure_telemetry", None) if telem_svc else None
            if callable(reconf_fn):
                target = ip if (str(ip).startswith("http://") or str(ip).startswith("https://") or "/api" in str(ip)) else host
                reconf_fn(enabled=connected, host=target, port=port)

            responder(True, {"message": "Configurações de telemetria salvas com sucesso."})
        except Exception as e:
            responder(False, error=str(e))

    def handle_test_telemetry_connection(self, msg: IpcMessage, responder: Responder) -> None:
        def _run_test():
            try:
                from src.infrastructure.monitor_client import MonitorClient
                payload = msg.payload or {}
                ip = payload.get("ip", "")
                host = payload.get("host", "localhost")
                port = int(payload.get("port", 1883))
                target = ip if (str(ip).startswith("http://") or str(ip).startswith("https://") or "/api" in str(ip)) else host
                ok, message = MonitorClient.test_connection_detailed(target, port=port)
                responder(ok, {"success": ok, "message": message})
            except Exception as e:
                responder(False, error=f"Erro no teste de conexão: {str(e)}")

        threading.Thread(target=_run_test, daemon=True).start()
