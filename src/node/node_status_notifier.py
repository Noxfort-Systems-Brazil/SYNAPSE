# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Optional, Callable, Any
from src.domain.entities import SourceStatus
from src.interfaces.node import INodeStatusNotifier


class NodeStatusNotifier:
    """
    Handles dispatching sensor validation and lifecycle status transitions.
    Decouples individual Traffic Nodes from global state repositories and manager hierarchies.
    """

    def __init__(
        self,
        on_status_change: Optional[Callable[[str, SourceStatus], None]] = None,
        graph_manager: Optional[Any] = None
    ):
        self._on_status_change = on_status_change
        self._graph_manager = graph_manager

    def notify_status(self, source_id: str, status: SourceStatus) -> None:
        """Dispatches status updates to configured callbacks or central AppState."""
        if self._on_status_change is not None:
            self._on_status_change(source_id, status)
        else:
            app_state = getattr(self._graph_manager, "app_state", None) if self._graph_manager else None
            if app_state:
                for src in app_state.get_all_data_sources():
                    if src.id == source_id or app_state.get_element_for_source(src.id) == source_id:
                        src.status = status
