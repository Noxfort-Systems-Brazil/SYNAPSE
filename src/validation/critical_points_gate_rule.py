# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Critical Points & Sensory Consistency Gate Rule.

SOLID Compliance:
- [SRP] Validates multi-station critical points propagation, status counts consistency,
  radar measurement modality parity, derived variable tagging, and volume unit standardization.
"""

import re
from typing import Any, Dict, List
from src.validation.exceptions import ReportViolation
from src.validation.base_rule import PostMarkdownRule
from src.report.traffic_regime_classifier import TrafficRegimeClassifier


class CriticalPointsGateRule(PostMarkdownRule):
    """Audits comprehensive coverage of critical stations and terminology coherence."""

    def validate_post(
        self, markdown_text: str, report_data: Dict[str, Any], context: Any = None
    ) -> List[ReportViolation]:
        violations: List[ReportViolation] = []
        if not markdown_text:
            return violations

        sensors = report_data.get("sensors", [])
        if not sensors:
            return violations

        corridor_info = TrafficRegimeClassifier.classify_corridor(sensors)
        critical_stations = corridor_info.get("critical_stations", [])
        crit_count = len(critical_stations)

        # 1. Rule: All critical stations must appear in Section 1.2 and Action Recommendation
        exec_sec_m = re.search(r"(?:## PARTE I|## PART I|## 1\.)[\s\S]*?(?=(?:## PARTE II|## PART II|## 2\.)|\Z)", markdown_text, flags=re.IGNORECASE)
        exec_text = exec_sec_m.group(0) if exec_sec_m else ""

        for cs in critical_stations:
            cid = cs["id"]
            if cid not in exec_text:
                violations.append(
                    ReportViolation(
                        error_class=2,
                        title="Estação Crítica Omitida no Resumo Executivo",
                        message=f"A estação crítica '{cid}' ({cs['name']}) deve constar explicitamente na Seção 1.2.",
                        section="Resumo Executivo (1.2)",
                    )
                )

        # 2. Rule: Status count in summary must equal actual critical stations count
        count_match = re.search(r"(\d+)\s+(?:de|of)\s+(\d+)\s+(?:pontos|points)[\s\S]*?(?:em\s+regime\s+crítico|critical)", exec_text, re.IGNORECASE)
        if count_match:
            stated_crit = int(count_match.group(1))
            if stated_crit != crit_count:
                violations.append(
                    ReportViolation(
                        error_class=2,
                        title="Divergência na Contagem de Pontos Críticos",
                        message=f"O resumo declara {stated_crit} ponto(s) crítico(s), mas o cálculo das fichas identifica {crit_count}.",
                        section="Resumo Executivo (1.2)",
                    )
                )

        # 3. Rule: Radar measurement modality parity (pontual vs média espacial)
        sec2_m = re.search(r"(?:## PARTE II|## 2\.)[\s\S]*?(?=(?:## PARTE III|## 3\.|### 2\.2)|\Z)", markdown_text)
        sec2_text = sec2_m.group(0) if sec2_m else ""

        has_radar = any("radar" in str(s.get("equipmentType", "")).lower() or "doppler" in str(s.get("equipmentType", "")).lower() for s in sensors)
        if has_radar and "pontual" in sec2_text.lower():
            annex_m = re.search(r"(?:## ANEXO I|### ANEXO B|ANEXO B|ANEXO I)[\s\S]*?$", markdown_text)
            annex_text = annex_m.group(0) if annex_m else ""
            if "velocidade média espacial" in annex_text.lower() and "radar" in annex_text.lower():
                # Check if radar card specifically calls its speed "média espacial"
                if re.search(r"velocidade\s+média\s+espacial\s+de\s+[0-9]+[,\.][0-9]+\s*km/h\s+aferida\s+por\s+radar", annex_text, re.IGNORECASE):
                    violations.append(
                        ReportViolation(
                            error_class=4,
                            title="Incoerência na Descrição do Tipo de Medição do Radar",
                            message="O radar foi descrito como medição pontual na Seção 2, mas consta como 'média espacial' na Ficha da Estação.",
                            section="Anexo I (Ficha da Estação)",
                        )
                    )

        # 4. Rule: Volume unit standardization across all sections
        # Every mention of Volume de Fluxo should include or be followed by (veíc/h)
        volume_without_unit = re.search(r"Volume de Fluxo\s*(?!Veicular|\(veíc/h\)|veíc/h)", markdown_text)
        if volume_without_unit and "Volume de Fluxo [" in markdown_text:
            violations.append(
                ReportViolation(
                    error_class=4,
                    title="Rótulo ou Unidade de Volume Incompleto",
                    message="O volume de fluxo deve especificar a unidade (veíc/h) de forma padronizada em todas as fontes.",
                    section="Explicabilidade / Fichas",
                )
            )

        return violations
