# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
from src.services.template_loader import JSONTemplateLoader
from src.interfaces.prompts import ITemplateLoader


@pytest.fixture
def loader():
    return JSONTemplateLoader()


def test_implements_protocol(loader):
    assert isinstance(loader, ITemplateLoader)


def test_language_resolution(loader):
    assert loader.resolve_language("pt_BR") == "pt_br"
    assert loader.resolve_language("en_US") == "en"
    assert loader.resolve_language("es-es") == "es"
    assert loader.resolve_language("chinese") == "zh"
    assert loader.resolve_language("unknown") == "pt_br"


def test_register_language_extension(loader):
    loader.register_language("de-de", "de")
    assert loader.resolve_language("de-DE") == "de"


def test_register_template_in_memory(loader):
    tmpl = {"system": "Sys", "user": "Usr"}
    loader.register_template("test_agent", "pt-br", tmpl)
    loaded = loader.load_template("test_agent", "pt_BR")
    assert loaded == tmpl


def test_register_fallback(loader):
    fallback = {"system": "Fallback", "user": "Fallback user"}
    loader.register_fallback("custom_domain", fallback)
    loaded = loader.load_template("custom_domain", "unsupported_lang")
    assert loaded == fallback


def test_clear_cache(loader):
    tmpl = {"system": "Sys", "user": "Usr"}
    loader.register_template("test_cache", "en", tmpl)
    assert loader.load_template("test_cache", "en") == tmpl
    loader.clear_cache()
    # Now it should fall back to generic
    generic = loader.load_template("test_cache", "en")
    assert "Domain: test_cache" in generic["system"]
