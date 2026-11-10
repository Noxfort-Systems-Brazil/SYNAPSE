# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
ABNT NBR 10719 & NBR 14724 HTML Sheet Preview Exporter.

SOLID Compliance:
- [SRP] Exclusively coordinates the assembly of paginated A4 HTML preview sheets.
- [OCP] Delegated snippet generators and CSS rules in abnt_html_templates.py and abnt_html_pages.py.
Focuses strictly on Neural Sensor Fusion & Metrological Perception Auditing.
"""

from datetime import datetime
from typing import Dict, Any, Optional, Union
import html

from src.domain.official_report import OfficialReportData
from src.formatters.abnt_html_templates import (
    build_abnt_css,
    build_sensor_rows_html,
    build_executive_station_rows_html,
    build_safety_interventions_html,
    build_attributions_html,
    build_legal_html,
)
from src.formatters.abnt_html_pages import build_all_pages_html


class AbntHtmlPreviewExporter:
    """
    Renders official traffic engineering reports into paginated A4 HTML preview sheets.
    """

    def generate_html(
        self,
        report_data: Union[OfficialReportData, Dict[str, Any]],
        typography_options: Optional[Dict[str, Any]] = None
    ) -> str:
        opts = typography_options or {}
        font_family = opts.get("fontFamily", "Times New Roman")
        font_stack = '"Times New Roman", Times, serif' if font_family == "Times New Roman" else 'Arial, Helvetica, sans-serif'
        base_font_size = f"{opts.get('fontSize', 12)}pt"
        line_height = str(opts.get("lineSpacing", 1.5))
        alignment = opts.get("alignment", "justify")

        r = OfficialReportData.from_dict(report_data) if not isinstance(report_data, OfficialReportData) else report_data
        protocol = html.escape(str(r.get("protocol", "RELATORIO-TRAFEGO-2026")))
        process_num = html.escape(str(r.get("processNumber", "PA-SMT-2026/0001")))
        city_hall = html.escape(str(r.get("cityHall", "PREFEITURA DO MUNICÍPIO DE SÃO PAULO")))
        department = html.escape(str(r.get("department", "SECRETARIA MUNICIPAL DE MOBILIDADE URBANA E TRÂNSITO")))
        authority = html.escape(str(r.get("authorityName", "Gabriel Moraes")))
        authority_role = html.escape(str(r.get("authorityRole", "Autoridade de Trânsito / Auditor Pericial")))
        registration = html.escape(str(r.get("registrationNumber", "Matrícula Funcional nº 84.102-3")))
        timestamp_raw = r.get("timestamp", datetime.now().isoformat())
        months_pt = [
            "janeiro", "fevereiro", "março", "abril", "maio", "junho",
            "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"
        ]
        try:
            dt_obj = datetime.fromisoformat(str(timestamp_raw))
            dt_str = dt_obj.strftime("%d/%m/%Y às %H:%M:%S")
            month_name = months_pt[dt_obj.month - 1]
            official_date_str = f"São Paulo - SP, {dt_obj.day} de {month_name} de {dt_obj.year}"
        except Exception:
            dt_str = str(timestamp_raw)
            official_date_str = "São Paulo - SP"

        loc = r.get("location", {})
        corridor_name = html.escape(str(loc.get("corridorName", "Corredor Arterial Central — Eixo Norte-Sul")))
        jurisdiction_name = html.escape(str(loc.get("jurisdiction", "Circunscrição Municipal")))
        system_ver = html.escape(str(r.get("systemVersion", "v2.0 Enterprise")))

        net = r.get("networkSummary", {})
        sensors = r.get("sensors", [])
        attributions = r.get("attributions", [])
        interventions = r.get("safetyInterventions", [])

        junctions_cnt = net.get("monitoredJunctionsCount", net.get("controlledIntersections", len(sensors) or 4))
        sensors_cnt = net.get("totalSensorsOnline", net.get("totalSensorsCount", len(sensors) or 4))
        avg_spd = net.get("averageCorridorSpeed", net.get("networkMeanSpeed", "18.4 km/h"))
        sat_idx = net.get("globalSaturationIndex", str(net.get("networkMeanSaturation", "0,70")).split()[0])
        flow_lbl = net.get("flowStateLabel", "Estável / Controlado")
        hourly_flow = net.get("totalHourlyFlow", "4.800 veíc/h")

        css_styles = build_abnt_css(font_stack, base_font_size, line_height, alignment)
        exec_station_rows = build_executive_station_rows_html(sensors, attributions)
        sensor_rows = build_sensor_rows_html(sensors)
        safety_rows = build_safety_interventions_html(interventions)
        attrs_html = build_attributions_html(attributions)
        legal_html = build_legal_html(r.get("legalFraming", []))

        refs = r.get("references", [
            "ASSOCIAÇÃO BRASILEIRA DE NORMAS TÉCNICAS. ABNT NBR 10719: Informação e documentação — Relatório técnico e/ou científico — Apresentação. Rio de Janeiro: ABNT, 2015.",
            "BRASIL. Lei Federal nº 9.503, de 23 de setembro de 1997. Institui o Código de Trânsito Brasileiro. Brasília, 1997.",
            "CONTRAN. Resolução nº 798/2020. Requisitos técnicos mínimos para medidores e sensores de trânsito. Brasília, 2020.",
            "LIGHTHILL, M. J.; WHITHAM, G. B. On kinematic waves II. A theory of traffic flow on long crowded roads. Proceedings of the Royal Society of London. Series A, Mathematical and Physical Sciences, v. 229, n. 1178, p. 317-345, 1955.",
            "SUNDARARAJAN, M.; TALY, A.; YAN, Q. Axiomatic Attribution for Deep Networks. In: International Conference on Machine Learning (ICML 2017). Sydney, Australia: PMLR, v. 70, p. 3319-3328, 2017.",
            "LIU, Y. et al. iTransformer: Inverted Transformers are Effective for Time Series Forecasting. In: ICLR, 2024.",
            "KOKHLIKYAN, N. et al. Captum: A unified and generic model interpretability library for PyTorch. arXiv:2009.07896, 2020."
        ])
        refs_html = "".join(f'<li class="mb-1.5 text-[10px] text-justify leading-snug">{html.escape(ref)}</li>' for ref in refs)

        page_ctx = {
            "city_hall": city_hall,
            "department": department,
            "protocol": protocol,
            "process_num": process_num,
            "dt_str": dt_str,
            "official_date_str": official_date_str,
            "system_ver": system_ver,
            "corridor_name": corridor_name,
            "jurisdiction_name": jurisdiction_name,
            "authority": authority,
            "authority_role": authority_role,
            "registration": registration,
            "audit_objective": html.escape(str(r.get("auditObjective", "Auditar a fusão neural de sensores heterogêneos e a consistência metrológica da malha arterial."))),
            "junctions_cnt": junctions_cnt,
            "sensors_cnt": sensors_cnt,
            "avg_spd": avg_spd,
            "hourly_flow": hourly_flow,
            "sat_idx": sat_idx,
            "flow_lbl": flow_lbl,
            "exec_station_rows": exec_station_rows,
            "observed_traffic_diagnosis": html.escape(str(r.get("observedTrafficDiagnosis", "Supervisão operacional contínua na malha arterial."))),
            "adaptive_action_executed": html.escape(str(r.get("adaptiveActionExecuted", "Fusão neural multi-sensorial executada pelo modelo iTransformer + GATv2 com filtragem cinemática PI-DVAE-TCN e transmissão via HFT-Link gRPC."))),
            "comparative_summary": html.escape(str(r.get("comparativeEvolution", {}).get("summaryText", "Linha de base metrológica inicial arquivada."))),
            "sensor_rows": sensor_rows,
            "safety_rows": safety_rows,
            "attrs_html": attrs_html,
            "counterfactual_analysis": html.escape(str(r.get("counterfactualAnalysis", "A ativação do KSE e da quarentena Zero-Trust seria dispensada se as leituras permanecessem estritamente no envelope gaussiano nominal."))),
            "legal_html": legal_html,
            "refs_html": refs_html,
        }

        pages_html = build_all_pages_html(page_ctx)

        return f"""
        {css_styles}
        <div class="abnt-container text-black">
{pages_html}
        </div>
        """
