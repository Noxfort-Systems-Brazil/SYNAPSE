# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
from src.services.prompt_formatter import ChatPromptBuilder, _SafeFormatter
from src.interfaces.prompts import IPromptBuilder


@pytest.fixture
def builder():
    return ChatPromptBuilder()


def test_implements_protocol(builder):
    assert isinstance(builder, IPromptBuilder)


def test_safe_formatter_missing_key():
    formatter = _SafeFormatter({"present": "value"})
    template = "Var: {present}, Missing: {missing}"
    assert template.format_map(formatter) == "Var: value, Missing: {missing}"


def test_build_messages_with_kwargs(builder):
    template = {
        "system": "System for {role} on stream {stream_id}.",
        "user": "Data value: {value}."
    }
    messages = builder.build_messages(
        template,
        role="Auditor",
        stream_id="cam_01",
        value=42.5
    )
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "System for Auditor on stream cam_01."
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "Data value: 42.5."


def test_build_messages_legacy_parameters(builder):
    template = {
        "system": "System {source}",
        "user": "Status: {status}, Values: {values}"
    }
    messages = builder.build_messages(
        template,
        source="sensor_01",
        status="WARNING",
        values=[1, 2, 3]
    )
    assert len(messages) == 2
    assert messages[0]["content"] == "System sensor_01"
    assert "Status: WARNING" in messages[1]["content"]
    assert "Values: [1, 2, 3]" in messages[1]["content"]
