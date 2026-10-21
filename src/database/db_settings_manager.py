# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import logging
import configparser
from typing import Dict, Any, Optional
from src.database.db_interfaces import ISettingsManager

logger = logging.getLogger("Synapse.DatabaseSettingsManager")


class DatabaseSettingsManager(ISettingsManager):
    """
    Manages reading and writing configuration to config/settings.ini.
    Adheres to Single Responsibility Principle (SRP) by isolating configuration I/O
    from database engine execution and telemetry services.
    """

    def __init__(self, settings_path: Optional[str] = None):
        if settings_path:
            self.settings_path = os.path.abspath(settings_path)
        else:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            self.settings_path = os.path.join(project_root, "config", "settings.ini")

        self.config_parser = configparser.ConfigParser()
        self._reload_ini()

    def _reload_ini(self) -> None:
        """Reloads the INI configuration from disk if the file exists."""
        if not os.path.exists(self.settings_path):
            example_path = f"{self.settings_path}.example"
            if os.path.exists(example_path):
                try:
                    import shutil
                    os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
                    shutil.copyfile(example_path, self.settings_path)
                    logger.info(f"[SETTINGS_MGR] Initialized {self.settings_path} from {example_path}")
                except Exception as e:
                    logger.warning(f"[SETTINGS_MGR] Failed copying {example_path} to {self.settings_path}: {e}")

        if os.path.exists(self.settings_path):
            try:
                self.config_parser.read(self.settings_path, encoding="utf-8")
            except Exception as e:
                logger.warning(f"[SETTINGS_MGR] Failed reading settings from {self.settings_path}: {e}")

    def _get_ini_val(self, section: str, key1: str, key2: Optional[str] = None, fallback: str = "") -> str:
        """Retrieves a configuration value checking key1 and optional key2 alias."""
        if self.config_parser.has_section(section):
            if self.config_parser.has_option(section, key1):
                return self.config_parser.get(section, key1)
            if key2 and self.config_parser.has_option(section, key2):
                return self.config_parser.get(section, key2)
        return fallback

    def load_database_settings(self) -> Dict[str, Any]:
        """Loads normalized database settings from config/settings.ini."""
        self._reload_ini()
        return {
            "db_type": self._get_ini_val("DATABASE", "db_type", fallback="postgres"),
            "host": self._get_ini_val("DATABASE", "host", "db_host", fallback="localhost"),
            "port": int(self._get_ini_val("DATABASE", "port", "db_port", fallback="5432")),
            "user": self._get_ini_val("DATABASE", "user", "db_user", fallback="user_synapse"),
            "password": self._get_ini_val("DATABASE", "password", "db_password", fallback=""),
            "dbname": self._get_ini_val("DATABASE", "dbname", "db_name", fallback="synapse_db"),
            "schema": self._get_ini_val("DATABASE", "schema", "db_schema", fallback="schema_synapse"),
            "connected": self._get_ini_val("DATABASE", "connected", fallback="false").lower() in ("true", "1", "yes"),
            "setup_done": self._get_ini_val("DATABASE", "setup_done", fallback="false").lower() in ("true", "1", "yes"),
        }

    def save_database_settings(self, config_dict: Dict[str, Any]) -> None:
        """Persists updated connection settings to config/settings.ini."""
        try:
            self._reload_ini()
            if not self.config_parser.has_section("DATABASE"):
                self.config_parser.add_section("DATABASE")

            for k, v in config_dict.items():
                self.config_parser.set("DATABASE", str(k), str(v))

            # Canonical alias mapping
            canonical_map = {
                "host": "db_host",
                "port": "db_port",
                "user": "db_user",
                "password": "db_password",
                "dbname": "db_name",
                "schema": "db_schema",
            }
            for k, alias in canonical_map.items():
                if k in config_dict:
                    self.config_parser.set("DATABASE", alias, str(config_dict[k]))
                elif alias in config_dict:
                    self.config_parser.set("DATABASE", k, str(config_dict[alias]))

            os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
            with open(self.settings_path, "w", encoding="utf-8") as f:
                self.config_parser.write(f)
            logger.info(f"[SETTINGS_MGR] Database settings saved to {self.settings_path}")
        except Exception as e:
            logger.error(f"[SETTINGS_MGR] Failed to save settings to {self.settings_path}: {e}")
            raise

    def load_telemetry_settings(self) -> Dict[str, Any]:
        """Loads telemetry settings from config/settings.ini."""
        self._reload_ini()
        ip = self._get_ini_val("TELEMETRY", "ip", fallback="localhost")
        host = self._get_ini_val("TELEMETRY", "host", fallback="localhost")
        port = int(self._get_ini_val("TELEMETRY", "port", fallback="1883"))
        connected = self._get_ini_val("TELEMETRY", "connected", fallback="false").lower() in ("true", "1", "yes")
        is_http = str(ip).startswith("http://") or str(ip).startswith("https://") or "/api" in str(ip)
        protocol = self._get_ini_val("TELEMETRY", "protocol", fallback="HTTP" if is_http else "MQTT")
        return {
            "ip": ip,
            "host": host,
            "port": port,
            "connected": connected,
            "protocol": protocol,
        }

    def save_telemetry_settings(self, ip: str, host: str, port: int, connected: bool) -> None:
        """Saves telemetry settings to config/settings.ini."""
        try:
            self._reload_ini()
            if not self.config_parser.has_section("TELEMETRY"):
                self.config_parser.add_section("TELEMETRY")
            self.config_parser.set("TELEMETRY", "ip", str(ip))
            self.config_parser.set("TELEMETRY", "host", str(host))
            self.config_parser.set("TELEMETRY", "port", str(port))
            self.config_parser.set("TELEMETRY", "connected", "true" if connected else "false")
            is_http = str(ip).startswith("http://") or str(ip).startswith("https://") or "/api" in str(ip)
            self.config_parser.set("TELEMETRY", "protocol", "HTTP" if is_http else "MQTT")

            os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
            with open(self.settings_path, "w", encoding="utf-8") as f:
                self.config_parser.write(f)
            logger.info(f"[SETTINGS_MGR] Telemetry settings saved to {self.settings_path}")
        except Exception as e:
            logger.error(f"[SETTINGS_MGR] Failed to save telemetry settings: {e}")
            raise

    def load_duckdns_settings(self) -> Dict[str, Any]:
        """Loads DuckDNS and Caddy settings from config/settings.ini."""
        self._reload_ini()
        enabled = self._get_ini_val("DUCKDNS", "enabled", fallback="false").lower() in ("true", "1", "yes")
        domain = self._get_ini_val("DUCKDNS", "domain", fallback="")
        token = self._get_ini_val("DUCKDNS", "token", fallback="")
        caddy_enabled = self._get_ini_val("DUCKDNS", "caddy_enabled", fallback="true").lower() in ("true", "1", "yes")
        port = int(self._get_ini_val("DUCKDNS", "port", fallback="8081"))
        https_port = int(self._get_ini_val("DUCKDNS", "https_port", fallback="443"))
        refresh_min = int(self._get_ini_val("DUCKDNS", "refresh_interval_min", fallback="10"))

        return {
            "enabled": enabled,
            "domain": domain,
            "token": token,
            "caddy_enabled": caddy_enabled,
            "port": port,
            "https_port": https_port,
            "refresh_interval_min": refresh_min,
        }

    def save_duckdns_settings(self, config_dict: Dict[str, Any]) -> None:
        """Saves DuckDNS and Caddy settings to config/settings.ini."""
        try:
            self._reload_ini()
            if not self.config_parser.has_section("DUCKDNS"):
                self.config_parser.add_section("DUCKDNS")

            for k, v in config_dict.items():
                if isinstance(v, bool):
                    self.config_parser.set("DUCKDNS", k, "true" if v else "false")
                else:
                    self.config_parser.set("DUCKDNS", k, str(v))

            os.makedirs(os.path.dirname(self.settings_path), exist_ok=True)
            with open(self.settings_path, "w", encoding="utf-8") as f:
                self.config_parser.write(f)
            logger.info(f"[SETTINGS_MGR] DuckDNS settings saved to {self.settings_path}")
        except Exception as e:
            logger.error(f"[SETTINGS_MGR] Failed to save DuckDNS settings: {e}")
            raise

