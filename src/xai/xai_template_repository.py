# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import os
import json
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger("Synapse.XAI.TemplateRepository")


class XaiTemplateRepository:
    """
    Central repository for modular XAI configuration files and localized report templates.
    Follows Single Responsibility (SRP) and Open-Closed (OCP) principles
    with in-memory caching.
    """

    _cached_templates: Optional[Dict[str, Any]] = None
    _cached_categories: Optional[Dict[str, Any]] = None

    CONFIG_FILES = [
        "xai_report_sections.json",
        "xai_equations.json",
        "xai_categories.json",
        "xai_table_templates.json",
        "xai_card_templates.json",
        "xai_glossary_limits.json",
    ]

    @classmethod
    def _find_config_path(cls, filename: str) -> Optional[str]:
        """Resolves absolute path of configuration file across environment directories."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(base_dir, "..", "..", "config", "templates", "xai", filename),
            os.path.join(base_dir, "..", "config", "templates", "xai", filename),
            os.path.join(os.getcwd(), "config", "templates", "xai", filename),
            os.path.join(base_dir, "..", "..", "config", filename),
            os.path.join(os.getcwd(), "config", filename),
        ]
        for p in candidates:
            if os.path.isfile(p):
                return os.path.abspath(p)
        return None

    @classmethod
    def _read_json_file(cls, filename: str) -> Dict[str, Any]:
        """Reads and parses a single JSON configuration file safely."""
        path = cls._find_config_path(filename)
        if not path:
            logger.debug(f"[XaiTemplateRepository] File not found: {filename}")
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"[XaiTemplateRepository] Failed reading {filename}: {e}")
            return {}

    @classmethod
    def load_all_templates(cls, force_reload: bool = False) -> Dict[str, Any]:
        """
        Loads and aggregates all modular XAI JSON template files into a unified dictionary.
        Returns a dictionary keyed by language code ('pt_br', 'en', etc.).
        """
        if cls._cached_templates is not None and not force_reload:
            return cls._cached_templates

        merged: Dict[str, Any] = {}
        for filename in cls.CONFIG_FILES:
            data = cls._read_json_file(filename)
            for key, val in data.items():
                if key in ("subscript_rules", "document_layout"):
                    merged[key] = val
                elif isinstance(val, dict):
                    if key not in merged:
                        merged[key] = {}
                    if filename == "xai_categories.json":
                        merged[key]["categories"] = val
                    else:
                        merged[key].update(val)

        cls._cached_templates = merged
        return merged

    @classmethod
    def load_categories(cls, language: Optional[str] = None, force_reload: bool = False) -> Dict[str, Any]:
        """Loads sensor category definitions directly from xai_categories.json."""
        if cls._cached_categories is None or force_reload:
            cls._cached_categories = cls._read_json_file("xai_categories.json")

        data = cls._cached_categories or {}
        if language:
            lang_key = language.lower().replace("-", "_")
            return data.get(lang_key, data.get("pt_br", {}))
        return data

    @classmethod
    def _normalize_lang_key(cls, language: str) -> str:
        """Normalizes language code into standard template keys (e.g. en_US -> en_us)."""
        raw = (language or "pt_br").lower().replace("-", "_").strip()
        if raw.startswith("en"):
            return "en_us"
        if raw.startswith("es"):
            return "es_es"
        if raw.startswith("pt"):
            return "pt_br"
        if raw.startswith("fr"):
            return "fr_fr"
        if raw.startswith("ru"):
            return "ru_ru"
        if raw.startswith("zh"):
            return "zh_cn"
        return raw

    @classmethod
    def get_templates_for_language(cls, language: str = "pt_br") -> Dict[str, Any]:
        """Retrieves aggregated templates dictionary for a specific language with pt_br fallback."""
        all_templates = cls.load_all_templates()
        lang_key = cls._normalize_lang_key(language)
        pt_tmpl = all_templates.get("pt_br", {})
        target_tmpl = all_templates.get(lang_key, {})

        # Merge target language over pt_br base to ensure zero missing keys
        lang_tmpl = dict(pt_tmpl)
        lang_tmpl.update(target_tmpl)

        # Resolve categories dictionary
        all_cats = all_templates.get("categories", {})
        cats = all_cats.get(lang_key, all_cats.get("pt_br", {}))
        lang_tmpl["categories"] = cats

        if "document_layout" in all_templates and "document_layout" not in lang_tmpl:
            lang_tmpl["document_layout"] = all_templates["document_layout"]

        if "subscript_rules" in all_templates and "subscript_rules" not in lang_tmpl:
            lang_tmpl["subscript_rules"] = all_templates["subscript_rules"]

        return lang_tmpl
