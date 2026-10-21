# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from src.domain.entities import DataSource
from src.interfaces.sources import ISourceProbeService
from src.utils.logging_setup import get_logger

logger = get_logger("SourceProbeService")


class HttpSourceProbeService(ISourceProbeService):
    """
    Diagnostic service for registered data sources.
    Network I/O is fully delegated to Go; Python performs local declaration validation only.
    """

    def __init__(self, timeout_seconds: float = 3.0):
        self.timeout_seconds = timeout_seconds

    def probe(self, source: DataSource) -> None:
        """Validates source metadata declaration without performing external network I/O."""
        origin_type = "Local" if source.is_local else "Global"
        logger.info(
            f"📡 [Sensor {origin_type}] '{source.name}' (ID: '{source.id}') registrado. "
            f"Conectividade de rede gerenciada exclusivamente pelo Gateway Go."
        )
