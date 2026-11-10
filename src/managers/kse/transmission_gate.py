# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Tuple, Optional, Any
from src.domain.entities import SourceType, SourceStatus


class CarinaTransmissionGate:
    """Evaluates whether transmission to CARINA is authorized (Local + Global validation)."""

    @staticmethod
    def evaluate(
        app_state: Any,
        is_warmup_complete: bool,
        rejection_warned: bool
    ) -> Tuple[bool, bool, bool, Optional[str]]:
        """
        Returns:
            (authorized, is_warmup_complete, rejection_warned, log_message)
        """
        if is_warmup_complete:
            return True, True, rejection_warned, None

        get_sources_fn = getattr(app_state, "get_all_data_sources", None)
        if not callable(get_sources_fn):
            return False, False, rejection_warned, None

        all_sources = get_sources_fn() or []
        live_sources = [
            s for s in all_sources
            if s.source_type != SourceType.SUMO_NET_XML
            and not (isinstance(s.connection_string, str) and s.connection_string.endswith(".parquet"))
            and "Historical Base" not in s.name
        ]

        active_locals = [s for s in live_sources if s.is_local and s.status == SourceStatus.ACTIVE]
        active_globals = [s for s in live_sources if not s.is_local and s.status == SourceStatus.ACTIVE]

        if active_locals and active_globals:
            local_names = ", ".join(s.name for s in active_locals)
            global_names = ", ".join(s.name for s in active_globals)
            msg = (
                f"[KSE] 🚀 Transmissão para CARINA liberada! "
                f"Sensores ativos validados: LOCAL ({local_names}) | GLOBAL ({global_names})."
            )
            return True, True, rejection_warned, msg

        # Check if all local or all global sensors were rejected
        non_rejected_locals = [s for s in live_sources if s.is_local and s.status != SourceStatus.REJECTED]
        non_rejected_globals = [s for s in live_sources if not s.is_local and s.status != SourceStatus.REJECTED]

        if live_sources and (not non_rejected_locals or not non_rejected_globals):
            if not rejection_warned:
                missing_type = "LOCAL" if not non_rejected_locals else "GLOBAL"
                msg = f"[KSE] ⛔ Transmissão para CARINA bloqueada: Nenhum sensor {missing_type} válido restante após descarte."
                return False, False, True, msg

        return False, False, rejection_warned, None
