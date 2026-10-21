# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Network Information and Diagnostics Service (SOLID: SRP).

Encapsulates low-level socket operations and local network metadata resolution.
"""

import socket
from typing import Dict, Any, Optional


class NetworkService:
    """Provides local network interface metadata."""

    @staticmethod
    def get_local_ip() -> str:
        """Determines the primary local outbound IP address."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("10.254.254.254", 1))
                return s.getsockname()[0]
        except Exception:
            return "127.0.0.1"

    @classmethod
    def get_network_info(cls, default_port: Optional[int] = None) -> Dict[str, Any]:
        """Returns standard network information payload, resolving unified DuckDNS endpoint if active."""
        import os
        gw_port = int(os.getenv("SYNAPSE_GATEWAY_PORT", "8081"))
        local_ip = cls.get_local_ip()

        duckdns_enabled = False
        duckdns_domain = ""
        https_port = 443
        unified_endpoint = f"http://{local_ip}:{gw_port}"
        unified_host = local_ip

        try:
            from src.database.db_settings_manager import DatabaseSettingsManager
            duck_cfg = DatabaseSettingsManager().load_duckdns_settings()
            enabled = duck_cfg.get("enabled", False)
            raw_domain = duck_cfg.get("domain", "").strip().lower()
            https_port = int(duck_cfg.get("https_port", 443))

            clean = raw_domain.replace("https://", "").replace("http://", "").strip("/")
            if clean.endswith(".duckdns.org"):
                clean = clean[:-len(".duckdns.org")].strip()

            if enabled and clean:
                duckdns_enabled = True
                duckdns_domain = clean
                unified_host = f"{clean}.duckdns.org"
                if https_port == 443:
                    unified_endpoint = f"https://{clean}.duckdns.org"
                else:
                    unified_endpoint = f"https://{clean}.duckdns.org:{https_port}"
        except Exception:
            pass

        return {
            "local_ip": local_ip,
            "default_port": default_port or gw_port,
            "gateway_port": gw_port,
            "duckdns_enabled": duckdns_enabled,
            "duckdns_domain": duckdns_domain,
            "https_port": https_port,
            "unified_endpoint": unified_endpoint,
            "unified_host": unified_host,
        }

