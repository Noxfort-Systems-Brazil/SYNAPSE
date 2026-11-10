# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import re
from typing import Any, Dict, List
from src.xai.report_block_base import ReportBlockBase


class ReportGuardianTableRenderer(ReportBlockBase):
    """
    Renders Zero-Trust safety safeguards, sensor quarantine, and kinematic reconstruction audit tables.
    """

    def render(self, lines: List[str], block: Dict[str, Any], context: Dict[str, Any]) -> None:
        interventions = context.get("safety_interventions", [])

        title_key = block.get("title_key", "")
        if title_key and self._t(title_key):
            lines.append(self._t(title_key))

        if not interventions:
            lines.append("Nenhuma salvaguarda foi acionada no período analisado.")
            lines.append("")
            return

        desc_key = block.get("desc_key", "")
        if desc_key and self._t(desc_key):
            lines.append(self._t(desc_key))
            lines.append("")

        table_hdr = self._t(
            block.get("header_template", "guardian_table_header"),
            "| Registro ID | Estação / Módulo | Irregularidade Detectada | Salvaguarda Aplicada | Estado Final |\n| :---: | :--- | :--- | :--- | :---: |"
        )
        lines.append(table_hdr)

        row_template = block.get("row_template", "guardian_table_row")
        for it in interventions:
            if isinstance(it, dict):
                reg_id = it.get("id", "REG-01")
                station_label = f"{it.get('junction', 'Estação')} • `{it.get('equipmentId', 'DET')}`"
                anomaly_desc = it.get("irregularityDetected", "Ruído instantâneo no sinal.")
                guard_applied = it.get("correctiveGuardrail", "Quarentena Zero-Trust aplicada.")
                final_state = it.get("finalState", "HOMOLOGADO")

                # Sanitize technical identifiers/enums into human-readable Portuguese without redundancy
                if "autoencoder convolucional" in guard_applied.lower():
                    guard_applied = re.sub(
                        r"autoencoder\s+convolucional\s+(?:Filtro\s+de\s+Ru[íi]do\s+Convolucional\s*)?\(?PI-DVAE\)?",
                        "autoencoder convolucional (PI-DVAE)",
                        guard_applied,
                        flags=re.IGNORECASE,
                    )
                else:
                    guard_applied = guard_applied.replace("PI_DVAE_CORRECTOR", "Filtro de Ruído Convolucional (PI-DVAE)")
                    guard_applied = guard_applied.replace("PI-DVAE", "Filtro de Ruído Convolucional (PI-DVAE)")

                guard_applied = guard_applied.replace("KSE_DEAD_RECKONING", "Dead Reckoning Cinemático (KSE)")
                guard_applied = guard_applied.replace("QUARENTENA_TEMPORAL", "Isolamento Preventivo em Quarentena")

                state_translations = {
                    "QUARENTENA_CONFIRMADA": "Leitura em Quarentena",
                    "FILTRADO_PI_DVAE": "Sinal Filtrado",
                    "ESTIMATIVA_CINEMÁTICA": "Projeção Temporária",
                }
                for k, v in state_translations.items():
                    if k in final_state:
                        final_state = final_state.replace(k, v)

                row_str = self._t(
                    row_template,
                    "| {reg_id} | {station_label} | {anomaly_desc} | {guard_applied} | **{final_state}** |",
                    reg_id=reg_id,
                    station_label=station_label,
                    anomaly_desc=anomaly_desc,
                    guard_applied=guard_applied,
                    final_state=final_state,
                )
                lines.append(row_str)

        lines.append("")
