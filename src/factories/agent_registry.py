# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Dict, Any, Optional


class AgentRegistry:
    """
    Dedicated in-memory Registry & Object Pool for active AI Agents per sensor source.
    
    SOLID Compliance (SRP):
    - Sole Responsibility: Stores, retrieves, and evicts active agent instances by source_id.
    - Zero creational logic: Does not instantiate neural networks or pipelines.
    """

    def __init__(self):
        # Internal storage: { source_id: { agent_type: instance } }
        self._registry: Dict[str, Dict[str, Any]] = {}

    def get(self, source_id: str, agent_type: str) -> Optional[Any]:
        """Retrieves an active agent instance for a given source and type."""
        return self._registry.get(source_id, {}).get(agent_type)

    def register(self, source_id: str, agent_type: str, agent: Any) -> None:
        """Registers an active agent instance under a given source and type."""
        if source_id not in self._registry:
            self._registry[source_id] = {}
        self._registry[source_id][agent_type] = agent

    def has(self, source_id: str, agent_type: str) -> bool:
        """Checks whether an agent of a given type exists for the source."""
        return agent_type in self._registry.get(source_id, {})

    def remove(self, source_id: str, agent_type: Optional[str] = None) -> None:
        """Removes a specific agent or all agents for a source."""
        if source_id in self._registry:
            if agent_type is not None:
                self._registry[source_id].pop(agent_type, None)
                if not self._registry[source_id]:
                    self._registry.pop(source_id, None)
            else:
                self._registry.pop(source_id, None)

    def clear(self) -> None:
        """Clears all registered agent instances."""
        self._registry.clear()
