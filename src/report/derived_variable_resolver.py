# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Canonical Derived Variable Resolver.

SOLID Compliance:
- [SRP] Single Source of Truth for traffic feature labels, units, and [Derivado por Modelo] tags.
- Guarantees 100% uniformity across Table 1.3, Section 3 XAI attributions, and Section 4 station narratives.
"""

import re
from typing import Optional


class DerivedVariableResolver:
    """Canonical resolver for traffic variable naming and derived model attribution tags."""

    TAG_DERIVED = "[Derivado por Modelo]"

    @classmethod
    def get_feature_name(
        cls,
        feature_type: str,
        is_feed: bool = False,
        source_category: str = "physical_radar",
        include_unit: bool = True,
    ) -> str:
        """
        Returns the standardized feature label across all report sections.
        """
        ft = feature_type.lower()
        if "spd" in ft or "velocidade" in ft:
            if is_feed or "feed" in source_category or "api" in source_category:
                base = "Velocidade Informada"
            elif "cam" in source_category or "visao" in source_category or "visão" in source_category:
                base = "Velocidade Estimada"
            else:
                base = "Velocidade Pontual"
            return f"{base} (km/h)" if include_unit else base

        elif "occ" in ft or "ocupa" in ft:
            base = "Taxa de Ocupação da Faixa"
            unit_str = " (%)" if include_unit else ""
            tag_str = f" {cls.TAG_DERIVED}" if is_feed else ""
            return f"{base}{unit_str}{tag_str}"

        elif "flow" in ft or "volume" in ft:
            base = "Volume de Fluxo Veicular"
            unit_str = " (veíc/h)" if include_unit else ""
            tag_str = f" {cls.TAG_DERIVED}" if is_feed else ""
            return f"{base}{unit_str}{tag_str}"

        elif "sat" in ft or "satura" in ft:
            base = "Grau de Saturação"
            unit_str = " (x = V/c)" if include_unit else ""
            tag_str = f" {cls.TAG_DERIVED}" if is_feed else ""
            return f"{base}{unit_str}{tag_str}"

        return feature_type

    @classmethod
    def clean_name_for_prose(cls, raw_name: str, keep_derived_tag: bool = True) -> str:
        """
        Strips unit parentheses (e.g. (%), (veíc/h), (km/h)) while strictly preserving
        [Derivado por Modelo] when keep_derived_tag is True.
        """
        has_derived = cls.TAG_DERIVED.lower() in raw_name.lower()
        # Remove parentheses and their contents: (km/h), (%), (veíc/h), (x = V/c)
        cleaned = re.sub(r"\s*\([^)]*\)", "", raw_name).strip()
        # Clean any existing brackets to normalize
        cleaned = re.sub(r"\s*\[[^\]]*\]", "", cleaned).strip()

        if has_derived and keep_derived_tag:
            return f"{cleaned} {cls.TAG_DERIVED}"
        return cleaned

    @classmethod
    def format_prose_mention(cls, name: str, keep_derived_tag: bool = True) -> str:
        """
        Formats a feature name with correct grammatical gender in Portuguese for narrative summaries.
        e.g. "a taxa de ocupação da faixa [Derivado por Modelo]" or "o volume de fluxo veicular [Derivado por Modelo]"
        """
        clean_name = cls.clean_name_for_prose(name, keep_derived_tag=keep_derived_tag)
        has_derived = cls.TAG_DERIVED.lower() in clean_name.lower()
        base_name = clean_name.replace(cls.TAG_DERIVED, "").strip().lower()
        tag_suffix = f" {cls.TAG_DERIVED}" if has_derived and keep_derived_tag else ""

        masculine_prefixes = ["volume", "fluxo", "grau", "fator", "peso", "índice", "resíduo"]
        if any(base_name.startswith(p) for p in masculine_prefixes):
            return f"o {base_name}{tag_suffix}"
        return f"a {base_name}{tag_suffix}"
