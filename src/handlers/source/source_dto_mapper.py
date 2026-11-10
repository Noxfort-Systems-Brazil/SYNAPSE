# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Any, Dict, Optional, List
from src.domain.entities import DataSource, SourceType


class SourceDtoMapper:
    """Transforms DataSource entities to IPC payload dictionaries and parses types."""

    @staticmethod
    def parse_source_type(raw_type: Optional[str], is_local: bool) -> SourceType:
        """Parses and normalizes raw string into SourceType enum."""
        if raw_type:
            if raw_type.upper() in SourceType.__members__:
                return SourceType[raw_type.upper()]
            for st in SourceType:
                if raw_type.lower() == st.value.lower():
                    return st
        return SourceType.MQTT if is_local else SourceType.API

    @staticmethod
    def resolve_element_name(app_state: Any, element_id: Optional[str]) -> Optional[str]:
        """Resolves human-friendly name of associated MapNode or MapEdge."""
        if not element_id or not app_state:
            return None

        get_edge_fn = getattr(app_state, "get_edge", None)
        if callable(get_edge_fn):
            edge = get_edge_fn(element_id)
            if edge and getattr(edge, "real_name", None):
                return edge.real_name

        get_node_fn = getattr(app_state, "get_node", None)
        if callable(get_node_fn):
            node = get_node_fn(element_id)
            if node and getattr(node, "real_name", None):
                return node.real_name

        return None

    @classmethod
    def to_summary_dto(cls, source: DataSource, app_state: Any) -> Dict[str, Any]:
        """Maps a DataSource entity to an IPC summary dictionary."""
        associated_element = None
        element_name = None
        if getattr(source, "is_local", True):
            get_elem_fn = getattr(app_state, "get_element_for_source", None)
            if callable(get_elem_fn):
                associated_element = get_elem_fn(source.id)
            else:
                sources_repo = getattr(app_state, "sources", None)
                repo_elem_fn = getattr(sources_repo, "get_element_for_source", None)
                if callable(repo_elem_fn):
                    associated_element = repo_elem_fn(source.id)

            element_name = cls.resolve_element_name(app_state, associated_element)

        return {
            "id": source.id,
            "name": source.name,
            "is_local": source.is_local,
            "status": getattr(source.status, "value", str(source.status)),
            "semantic_type": getattr(source, "semantic_type", None) or "Scanning...",
            "latest_value": getattr(source, "latest_value", None),
            "confidence_score": getattr(source, "confidence_score", None),
            "associated_element": associated_element,
            "associated_element_name": element_name,
            "connection_string": getattr(source, "connection_string", "") or "",
        }
