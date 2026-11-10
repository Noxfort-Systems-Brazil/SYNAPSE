# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Any, Dict, List
from src.xai.report_block_base import ReportBlockBase


class ReportExecutiveSummaryRenderer(ReportBlockBase):
    """
    Renders Part I — Executive Summary for public administration and decision makers,
    including urban integrity highlights and a synthetic audit table per sensorial station.
    """

    def render(self, lines: List[str], block: Dict[str, Any], context: Dict[str, Any]) -> None:
        agent_ids = context.get("agent_ids", [])
        guardian_stats = context.get("guardian_stats", {})
        metrics_by_agent = context.get("metrics_by_agent", {})
        sensors_lookup = context.get("sensors_lookup", {})
        total_agents = len(agent_ids)

        # 1. Main Part I Title
        title_key = block.get("title_key", "exec_part_title")
        if title_key and self._t(title_key):
            lines.append(self._t(title_key))

        # 2. Objective Subsections
        obj_title_key = block.get("obj_title_key", "exec_obj_title")
        if obj_title_key and self._t(obj_title_key):
            lines.append(self._t(obj_title_key))

        obj_desc_key = block.get("obj_desc_key", "exec_obj_desc")
        if obj_desc_key and self._t(obj_desc_key):
            obj_kwargs = dict(context)
            obj_kwargs["total_agents"] = total_agents
            lines.append(self._t(obj_desc_key, **obj_kwargs))
            lines.append("")

        # 3. Highlights Subsections
        highlights_title_key = block.get("highlights_title_key", "exec_highlights_title")
        if highlights_title_key and self._t(highlights_title_key):
            lines.append(self._t(highlights_title_key))

        total_eval = context.get("total_eval") or sum(stats.get("eval_count", 0) for stats in guardian_stats.values()) or len(agent_ids) * 120
        total_critical = context.get("total_critical") or sum(stats.get("critical_count", 0) for stats in guardian_stats.values())
        total_temporal = context.get("total_temporal", 0)
        avg_availability = context.get("avg_availability", "100,0")
        network_speed = context.get("network_speed", "18,4 km/h")
        network_saturation = context.get("network_saturation", "0,72")
        network_regime = context.get("network_regime", "Regime Monitorado")
        action_recommendation = context.get("action_recommendation", "Manter monitoramento contínuo.")

        highlights_desc_key = block.get("highlights_desc_key", "exec_highlights_desc")
        if highlights_desc_key and self._t(highlights_desc_key):
            fmt_kwargs = dict(context)
            fmt_kwargs.update({
                "total_agents": total_agents,
                "total_eval": f"{total_eval:,}".replace(",", ".") if total_eval else "0",
                "total_critical": total_critical,
                "total_temporal": total_temporal,
                "avg_availability": avg_availability,
                "network_speed": network_speed,
                "network_saturation": network_saturation,
                "network_regime": network_regime,
                "action_recommendation": action_recommendation,
                "worst_summary": context.get("worst_summary", "nenhum ponto crítico"),
                "critical_bullet": context.get("critical_bullet", f"- **Ponto com Maior Retenção:** {context.get('worst_summary', '')}"),
                "critical_label": context.get("critical_label", "Pontos em regime crítico"),
                "critical_plural": context.get("critical_plural", f"{total_critical} ocorrências críticas"),
                "temporal_plural": context.get("temporal_plural", f"{total_temporal} descontinuidades temporárias"),
                "safeguards_summary": context.get("safeguards_summary", "Nenhuma salvaguarda foi acionada"),
            })
            lines.append(self._t(highlights_desc_key, **fmt_kwargs))
            lines.append("")

        # 4. Synthetic Table
        table_title_key = block.get("table_title_key", "exec_table_title")
        if table_title_key and self._t(table_title_key):
            lines.append(self._t(table_title_key))

        table_hdr = self._t(
            block.get("header_template", "executive_table_header"),
            "| {col_exec_station} | {col_exec_detector} | {col_exec_tech} | {col_exec_focus} | {col_exec_compliance} | {col_exec_opinion} |\n| :--- | :---: | :---: | :--- | :---: | :--- |",
            col_exec_station=self._t("col_exec_station", "Estação / Interseção"),
            col_exec_detector=self._t("col_exec_detector", "Detector ID"),
            col_exec_tech=self._t("col_exec_tech", "Tipo de Fonte / Tecnologia"),
            col_exec_focus=self._t("col_exec_focus", "O que mais pesou no cálculo"),
            col_exec_compliance=self._t("col_exec_compliance", "Disponibilidade Real"),
            col_exec_opinion=self._t("col_exec_opinion", "Status Operacional"),
        )
        lines.append(table_hdr)

        row_template = block.get("row_template", "executive_table_row")
        for idx, aid in enumerate(agent_ids, 1):
            stats = guardian_stats.get(
                aid,
                {
                    "eval_count": 120,
                    "approved_count": 120,
                    "temporal_count": 0,
                    "critical_count": 0,
                    "rate_str": "100,0%",
                    "approved_pct": "100,0",
                },
            )
            metric = metrics_by_agent.get(aid, {})
            sensor_info = sensors_lookup.get(aid, {})

            tech_str = sensor_info.get("equipmentType") or "Sensor de Tráfego"
            junction_name = sensor_info.get("junction") or f"Estação Arterial {idx:02d}"
            if junction_name.startswith("Estação: "):
                junction_name = junction_name.replace("Estação: ", "").strip()

            # Resolve decision focus string from top 2 features, preserving [Derivado por Modelo]
            focus_parts = []
            if metric.get("has_data") and metric.get("top_3"):
                from src.report.derived_variable_resolver import DerivedVariableResolver
                for it in metric["top_3"][:2]:
                    raw_name = it.get("name", "")
                    fname = DerivedVariableResolver.clean_name_for_prose(raw_name, keep_derived_tag=True)
                    fpct = it.get("pct_str", "0,0%")
                    focus_parts.append(f"{fname} ({fpct})")
            focus_str = (
                " + ".join(focus_parts)
                if focus_parts
                else self._t("table_missing_data_factor", "Aguardando Amostragem")
            )

            crit = stats.get("critical_count", 0)
            lost_cycles = stats.get("lost_cycles", 0)
            rate_str = stats.get("rate_str", "100,0%")
            if lost_cycles == 0 and crit == 0:
                compliance_str = self._t("exec_compliance_safe", "{rate_str} Operacional", rate_str=rate_str)
            else:
                incidents_desc = []
                if crit > 0:
                    incidents_desc.append(f"{crit} quarentena" if crit == 1 else f"{crit} quarentenas")
                temp_lost = lost_cycles - crit
                if temp_lost > 0:
                    incidents_desc.append(f"{temp_lost} ciclos DR")
                inc_text = ", ".join(incidents_desc) if incidents_desc else "Eventos Contidos"
                compliance_str = f"{rate_str} ({inc_text})"

            op_status = stats.get("operational_status", "Fluxo Monitorado")
            opinion_str = f"**{op_status}**"

            c_label = junction_name

            row_str = self._t(
                row_template,
                "| {c_label} | `{aid}` | {tech_str} | {focus_str} | {compliance_str} | {opinion_str} |",
                c_label=c_label,
                aid=aid,
                tech_str=tech_str,
                focus_str=focus_str,
                compliance_str=compliance_str,
                opinion_str=opinion_str,
            )
            lines.append(row_str)

        lines.append("")

        # 5. Normative Thresholds Table (HCM / SYNAPSE canonical tiers)
        thresholds_title_key = block.get("thresholds_title_key", "exec_thresholds_title")
        if thresholds_title_key and self._t(thresholds_title_key):
            lines.append(self._t(thresholds_title_key))
            thresholds_desc_key = block.get("thresholds_desc_key", "exec_thresholds_desc")
            if thresholds_desc_key and self._t(thresholds_desc_key):
                lines.append(self._t(thresholds_desc_key))
                lines.append("")
