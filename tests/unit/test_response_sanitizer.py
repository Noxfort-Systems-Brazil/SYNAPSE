# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
from src.services.response_sanitizer import ResponseSanitizer
from src.interfaces.prompts import IResponseSanitizer


@pytest.fixture
def sanitizer():
    return ResponseSanitizer()


def test_implements_protocol(sanitizer):
    assert isinstance(sanitizer, IResponseSanitizer)


def test_empty_response(sanitizer):
    assert sanitizer.clean("") == ""
    assert sanitizer.clean(None) == ""


def test_clean_think_tags(sanitizer):
    raw = "<think>Step-by-step reasoning</think>Final answer."
    assert sanitizer.clean(raw) == "Final answer."


def test_clean_multiline_think_tags(sanitizer):
    raw = "<think>\nLine 1\nLine 2\n</think>\n\nVerdict rendered."
    assert sanitizer.clean(raw) == "Verdict rendered."


def test_clean_unclosed_think_tag(sanitizer):
    raw = "<think>Thinking until cutoff... Partial verdict"
    cleaned = sanitizer.clean(raw)
    assert "Partial verdict" in cleaned
    assert "<think>" not in cleaned


def test_clean_with_custom_callbacks(sanitizer):
    raw = "<think>reasoning</think> [FLAG_RED] Critical error."
    cleaned = sanitizer.clean(
        raw,
        cleaners=[lambda text: text.replace("[FLAG_RED]", "ALERT:")]
    )
    assert cleaned == "ALERT: Critical error."
