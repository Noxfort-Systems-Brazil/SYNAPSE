# SYNAPSE - A Gateway of Intelligent Perception for Traffic Management
# Copyright (C) 2026 Noxfort Systems
#
# File: src/handlers/source/source_guard.py
# Description: Security, lockdown and DuckDNS compliance guards for data sources (SOLID: SRP).

from typing import Optional, Any


class SourceGuard:
    """Enforces infrastructure and security policies for data source operations."""

    @staticmethod
    def check_lockdown(security_manager: Optional[Any]):
        """Raises RuntimeError if the system is currently under lockdown."""
        is_lockdown_fn = getattr(security_manager, "is_lockdown", None) if security_manager else None
        if callable(is_lockdown_fn) and is_lockdown_fn():
            raise RuntimeError("Operação bloqueada. O sistema está em estado de LOCKDOWN.")

    @staticmethod
    def ensure_local_sensor_prerequisites(is_local: bool):
        """
        Enforces DuckDNS active configuration before allowing registration/import of local sensors.
        """
        if not is_local:
            return

        try:
            from src.database.db_settings_manager import DatabaseSettingsManager
            duck_cfg = DatabaseSettingsManager().load_duckdns_settings()
            if not duck_cfg.get("enabled", False) or not str(duck_cfg.get("domain", "")).strip():
                raise ValueError(
                    "DuckDNS Obrigatório: Não é permitido cadastrar ou conectar sensores locais sem o DuckDNS configurado e ativo. Acesse Configurações > Acesso Remoto (DuckDNS)."
                )
        except ValueError:
            raise
        except Exception:
            pass
