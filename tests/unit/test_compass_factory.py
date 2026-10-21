# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest

from src.agents.compass_agent import CompassAgent
from src.factories.compass_factory import CompassFactory
from src.factories.agent_factory import AgentFactory


def test_compass_factory_and_agent_factory_lifecycle():
    """Verifies CompassFactory creation and AgentFactory get/release lifecycle."""
    agent = CompassFactory.create()
    assert isinstance(agent, CompassAgent)

    factory = AgentFactory(config={})
    compass = factory.get_or_create_compass("sensor_abc")
    assert isinstance(compass, CompassAgent)

    # Verify singleton retrieval for same source
    compass_same = factory.get_or_create_compass("sensor_abc")
    assert compass is compass_same

    # Release from memory
    factory.release_compass("sensor_abc")
    assert factory.registry.get("sensor_abc", "compass") is None
