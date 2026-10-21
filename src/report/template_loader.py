# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Report Template Loader and Municipal Configuration Resolver.

Loads and caches the normative traffic report template JSON file,
and merges municipal administrative metadata with defaults.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("Synapse.Report.TemplateLoader")

DEFAULT_TEMPLATE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "config", "traffic_report_template.json")
)


class TrafficReportTemplateLoader:
    """Loads and caches the normative template JSON file."""

    def __init__(self, template_path: Optional[str] = None):
        self.template_path = template_path or DEFAULT_TEMPLATE_PATH
        self._cached_template: Optional[Dict[str, Any]] = None

    def load_template(self) -> Dict[str, Any]:
        if self._cached_template is not None:
            return self._cached_template

        if os.path.isfile(self.template_path):
            try:
                with open(self.template_path, "r", encoding="utf-8") as f:
                    self._cached_template = json.load(f)
                    return self._cached_template
            except Exception as e:
                logger.error(f"Failed to load traffic report template: {e}")

        return {
            "systemVersion": "SYNAPSE v2.0 Enterprise (Gateway de Percepção)",
            "auditObjective": "Auditoria de Fusão Neural de Sensores.",
            "location": {},
            "safetyInterventions": [],
            "quesitos": [],
            "legalFraming": [],
            "references": [],
        }


class MunicipalConfigResolver:
    """Resolves municipal administrative metadata merging defaults with custom overrides."""

    @classmethod
    def resolve_municipal_config(
        cls,
        cfg: Optional[Dict[str, Any]],
        template: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        tpl = (template or {}).get("defaultAttribution", {})
        defaults = {
            "cityHall": tpl.get("cityHall", "PREFEITURA DO MUNICÍPIO DE SÃO PAULO"),
            "department": tpl.get("department", "SECRETARIA MUNICIPAL DE MOBILIDADE URBANA E TRÂNSITO (SMT)"),
            "authorityName": tpl.get("authorityName", "Gabriel Moraes"),
            "authorityRole": tpl.get("authorityRole", "Autoridade Municipal de Trânsito / Secretário de Mobilidade"),
            "registrationNumber": tpl.get("registrationNumber", "Matrícula Funcional nº 84.102-3 • Portaria SMT 142/2025"),
            "processPrefix": tpl.get("processPrefix", "PA-SMT-2026/"),
        }
        if cfg:
            defaults.update({k: v for k, v in cfg.items() if v is not None})
        return defaults
