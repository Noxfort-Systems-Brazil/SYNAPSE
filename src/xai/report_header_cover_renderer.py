# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

from typing import Any, Dict, List
from datetime import datetime
from src.xai.report_block_base import ReportBlockBase


class ReportHeaderCoverRenderer(ReportBlockBase):
    """
    Renders institutional municipal header and document identification metadata table
    in strict compliance with ABNT NBR 10719:2015.
    """

    def render(self, lines: List[str], block: Dict[str, Any], context: Dict[str, Any]) -> None:
        report_data = context.get("report_data", {})
        city_hall = report_data.get("cityHall") or "PREFEITURA DO MUNICÍPIO • PODER EXECUTIVO MUNICIPAL"
        department = report_data.get("department") or "SECRETARIA MUNICIPAL DE MOBILIDADE E TRÂNSITO"
        authority = report_data.get("authorityName") or "(A preencher pelo Responsável Técnico)"
        authority_role = report_data.get("authorityRole") or "Engenheiro de Tráfego / Responsável Técnico"
        registration = report_data.get("registrationNumber") or "CREA / ART a vincular"
        protocol = report_data.get("protocol") or "RELATORIO-TRAFEGO-2026-XAI"
        process_num = report_data.get("processNumber") or "A vincular (Protocolo SEI)"

        months_pt = [
            "janeiro", "fevereiro", "março", "abril", "maio", "junho",
            "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
        ]
        months = self.templates.get("months_names") or months_pt
        timestamp_raw = report_data.get("timestamp", datetime.now().isoformat())
        lang = str(context.get("language") or report_data.get("language", "pt_br")).lower()
        try:
            dt_obj = datetime.fromisoformat(str(timestamp_raw))
            dt_str = dt_obj.strftime("%d/%m/%Y às %H:%M:%S")
            month_name = months[dt_obj.month - 1]
            city_name = report_data.get("city", "São Paulo")
            state_uf = report_data.get("state_uf", "SP")
            if "en" in lang:
                official_date_str = f"{city_name} - {state_uf}, {month_name} {dt_obj.day}, {dt_obj.year}"
            else:
                official_date_str = f"{city_name} - {state_uf}, {dt_obj.day} de {month_name} de {dt_obj.year}"
        except Exception:
            dt_str = str(timestamp_raw)
            official_date_str = "São Paulo - SP"

        loc = report_data.get("location", {})
        corridor = loc.get("corridorName") or "Corredor Arterial Central — Eixo Norte-Sul"
        jurisdiction = loc.get("jurisdiction") or "Circunscrição Municipal"
        system_ver = report_data.get("systemVersion", "v2.0 Enterprise")
        sys_label = system_ver if "SYNAPSE" in system_ver else f"SYNAPSE {system_ver}"

        total_eval = context.get("total_eval") or (len(context.get("agent_ids", [])) * 120)
        num_sources = len(context.get("agent_ids", [])) or 4

        lines.append(self._t("cover_notice", "> **Aviso Operacional:** *Documento gerado automaticamente — rascunho técnico até validação pelo Responsável Técnico.*"))
        lines.append("")
        lines.append(self._t("cover_gov_title", "# REPÚBLICA FEDERATIVA DO BRASIL • PODER EXECUTIVO MUNICIPAL"))
        lines.append(f"### {city_hall} — {department}")
        lines.append(self._t("cover_superintendence", "**SUPERINTENDÊNCIA DE ENGENHARIA DE TRÁFEGO E OPERAÇÃO VIÁRIA**"))
        gw_desc = self._t("cover_gateway_desc", "Gateway de Percepção Inteligente e Fusão Neural de Sensores")
        lines.append(f"*{sys_label} ({gw_desc})*")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(f"> *{official_date_str}*")
        lines.append("")
        lines.append(self._t("cover_report_title", "# LAUDO TÉCNICO DE AUDITORIA DE TRÁFEGO — RELATÓRIO EXPLICATIVO DO SYNAPSE (XAI) Nº {protocol}", protocol=protocol))
        lines.append(self._t("cover_meta_line", "**Processo Administrativo:** `{process_num}` • **Horário de Referência:** `{dt_str} (UTC-03:00 / Horário de Brasília)` • **Sistema:** `v2.0 Enterprise`", process_num=process_num, dt_str=dt_str))
        lines.append("")
        lines.append(self._t("cover_ementa", "> **Assunto / Ementa:** *Auditoria de Inteligência Artificial, Explicabilidade Algorítmica (XAI), Salvaguardas Operacionais e Avaliação de Desempenho Operacional da Malha Viária Urbana.*"))
        lines.append("")
        lines.append(self._t("cover_id_table_title", "### Quadro de Identificação do Sistema e Contexto Operacional"))
        lines.append("")
        col_field = self._t("col_cover_field", "Campo de Identificação")
        col_spec = self._t("col_cover_spec", "Especificação Técnica do Monitoramento")
        lines.append(f"| {col_field} | {col_spec} |")
        lines.append("| :--- | :--- |")
        r_sys = self._t("cover_row_sys_id", "Identificador do Sistema")
        lines.append(f"| **{r_sys}** | {sys_label} |")
        r_corr = self._t("cover_row_corridor", "Corredor Monitorado")
        lines.append(f"| **{r_corr}** | {corridor} ({jurisdiction}) |")
        r_per = self._t("cover_row_period", "Período e Horário dos Dados")
        v_per = self._t("cover_period_val", "Referência em `{dt_str}` (Janela de 120s • Taxa contínua de 1,0s • Fuso UTC-03:00)", dt_str=dt_str)
        lines.append(f"| **{r_per}** | {v_per} |")
        r_samp = self._t("cover_row_samples", "Volume de Amostras")
        v_samp = self._t("cover_samples_val", "{total_eval} leituras de telemetria ({num_sources} fontes x 120 ciclos a 1,0 Hz)", total_eval=total_eval, num_sources=num_sources)
        lines.append(f"| **{r_samp}** | {v_samp} |")
        r_obj = self._t("cover_row_objective", "Objetivo da Estimativa")
        v_obj = self._t("cover_row_objective_val", "Reconstrução contínua da velocidade (usando medições pontuais como aproximação da velocidade espacial), densidade e saturação da malha viária")
        lines.append(f"| **{r_obj}** | {v_obj} |")
        r_eng = self._t("cover_row_engine", "Motor de Percepção / Fusão")
        v_eng = self._t("cover_row_engine_val", "iTransformer + GATv2 Lite (PINO / KSE) — Build Checksum: `7f8a3c9b`")
        lines.append(f"| **{r_eng}** | {v_eng} |")
        r_proc = self._t("cover_row_process", "Processo Administrativo")
        lines.append(f"| **{r_proc}** | `{process_num}` |")
        r_prot = self._t("cover_row_protocol", "Protocolo de Emissão")
        lines.append(f"| **{r_prot}** | `{protocol}` |")
        r_sup = self._t("cover_row_supervisor", "Supervisão / Responsável Técnico")
        lines.append(f"| **{r_sup}** | **{authority}** ({authority_role} — {registration}) |")

        sensors_list = report_data.get("sensors", [])
        has_enforcement_radar = any(
            ("radar" in str(s.get("equipmentType", "")).lower() or "doppler" in str(s.get("equipmentType", "")).lower()) and
            (bool(s.get("is_enforcement")) or "fiscaliz" in str(s.get("purpose", "")).lower() or "autua" in str(s.get("purpose", "")).lower() or "fiscaliz" in str(s.get("equipmentType", "")).lower())
            for s in sensors_list
        )
        has_personal_data = any(
            "placa" in str(s.get("equipmentType", "")).lower() or
            "lpr" in str(s.get("equipmentType", "")).lower() or
            "reconhecimento de placa" in str(s.get("equipmentType", "")).lower() or
            bool(s.get("processes_personal_data"))
            for s in sensors_list
        )
        applicable_standards = ["CTB Art. 24", "ABNT NBR 10719:2015"]
        if has_personal_data:
            applicable_standards.append("LGPD Art. 20")
        if has_enforcement_radar:
            applicable_standards.append("Resolução CONTRAN nº 798/2020")
        standards_str = ", ".join(applicable_standards)
        r_std = self._t("cover_row_standards", "Legislação e Normas de Referência")
        lines.append(f"| **{r_std}** | {standards_str} |")
        lines.append("")
        lines.append("---")
        lines.append("")
