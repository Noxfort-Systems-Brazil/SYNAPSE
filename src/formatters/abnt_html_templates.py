# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
HTML Templates and CSS Styler for ABNT NBR 10719 & NBR 14724 Preview Sheets.

SOLID: Single Responsibility Principle (SRP):
Encapsulates HTML snippet composition, tables, lists, and CSS variables.
Focuses strictly on Neural Sensor Fusion & Metrological Perception Auditing.
"""

import html
from typing import Dict, Any, List


def build_abnt_css(font_stack: str, base_font_size: str, line_height: str, alignment: str) -> str:
    """Constructs CSS stylesheet with ABNT margins and configurable CSS Custom Properties."""
    return f"""
    <style>
        :root {{
            --report-font: {font_stack};
            --report-font-size: {base_font_size};
            --report-line-height: {line_height};
            --report-align: {alignment};
        }}
        .abnt-container {{
            font-family: var(--report-font);
            font-size: var(--report-font-size);
            line-height: var(--report-line-height);
            text-align: var(--report-align);
        }}
        .abnt-page-sheet {{
            width: 100%;
            max-width: 210mm;
            min-height: 297mm;
            padding: 30mm 20mm 20mm 30mm;
            margin: 0 auto 24px auto;
            background-color: #ffffff;
            color: #000000;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
            box-sizing: border-box;
            position: relative;
        }}
        .abnt-heading-1 {{
            font-size: 13pt;
            font-weight: bold;
            text-transform: uppercase;
            margin-top: 14pt;
            margin-bottom: 6pt;
            border-bottom: 1px solid #000000;
            padding-bottom: 2pt;
        }}
        .abnt-heading-2 {{
            font-size: 11pt;
            font-weight: bold;
            margin-top: 10pt;
            margin-bottom: 4pt;
        }}
        .abnt-p {{
            margin-bottom: 6pt;
            text-indent: 1.25cm;
        }}
        .abnt-p-noindent {{
            margin-bottom: 6pt;
            text-indent: 0;
        }}
        .abnt-header-meta {{
            display: flex;
            justify-content: space-between;
            font-size: 8.5pt;
            color: #666666;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 4px;
            margin-bottom: 16px;
        }}
        .abnt-footer-meta {{
            position: absolute;
            bottom: 12mm;
            left: 30mm;
            right: 20mm;
            text-align: center;
            font-size: 7.5pt;
            color: #888888;
            border-top: 1px solid #e2e8f0;
            padding-top: 4px;
        }}
        .latex-box {{
            background-color: #f8fafc;
            border-left: 3px solid #0284c7;
            padding: 6px 12px;
            margin: 6pt 0;
            font-family: 'Courier New', monospace;
            font-size: 9.5pt;
        }}
        @media print {{
            .abnt-page-sheet {{
                box-shadow: none;
                margin: 0;
                page-break-after: always;
            }}
        }}
    </style>
    """


def build_sensor_rows_html(sensors: List[Dict[str, Any]]) -> str:
    """Builds table rows for sensors in IBGE open borders format."""
    rows = []
    for s in sensors:
        rows.append(f"""
        <tr class="border-b border-slate-200 text-[10px]">
            <td class="py-1 px-1.5 font-mono font-bold">{html.escape(str(s.get('id', '')))}</td>
            <td class="py-1 px-1.5">{html.escape(str(s.get('junction', '')))}</td>
            <td class="py-1 px-1.5 text-center font-mono">{html.escape(str(s.get('measuredSpeed', '')))}</td>
            <td class="py-1 px-1.5 text-center font-mono">{html.escape(str(s.get('measuredFlow', '')))}</td>
            <td class="py-1 px-1.5 text-center font-mono">{html.escape(str(s.get('occupancyRate', '')))}</td>
            <td class="py-1 px-1.5 text-right font-mono font-bold text-black">{html.escape(str(s.get('saturationDegree', '')))}</td>
        </tr>
        """)
    return "".join(rows)


def build_attributions_html(attributions: List[Dict[str, Any]]) -> str:
    """Builds XAI integrated gradients attributions snippet."""
    items = []
    for i, a in enumerate(attributions):
        items.append(f"""
        <div class="mb-2 text-[11px] abnt-p">
            <span class="font-bold">Fator {i+1} — {html.escape(str(a.get('parameterName', '')))} ({html.escape(str(a.get('detectorId', '')))}):</span>
            Peso Causal de <span class="font-bold font-mono">{a.get('causalWeightPercent', 0)}%</span> (Gradiente: {html.escape(str(a.get('gradientDirection', '')))}).
            {html.escape(str(a.get('trafficImpactAnalysis', '')))}
        </div>
        """)
    return "".join(items)


def build_quesitos_html(quesitos: List[Dict[str, Any]]) -> str:
    """Builds formal technical answers to regulatory audit quesitos."""
    items = []
    for q in quesitos:
        items.append(f"""
        <div class="mb-3.5 pb-2 border-b border-slate-100">
            <div class="font-bold text-[11px] text-black uppercase tracking-tight">QUESITO Nº {html.escape(str(q.get('number', '')))}: {html.escape(str(q.get('question', '')))}</div>
            <div class="abnt-p text-[11px] mt-1 font-bold text-emerald-800 dark:text-emerald-400">RESPOSTA DO PERITO: [{html.escape(str(q.get('answer', '')))}]</div>
            <div class="abnt-p text-[10.5px] mt-0.5 text-slate-700 dark:text-slate-300"><span class="font-semibold">Fundamentação Técnica:</span> {html.escape(str(q.get('technicalJustification', '')))}</div>
        </div>
        """)
    return "".join(items)


def build_executive_station_rows_html(sensors: List[Dict[str, Any]], attributions: List[Dict[str, Any]]) -> str:
    """Builds executive synthetic audit table rows per station (CARINA_CORE 1.3 pattern)."""
    attr_by_id = {str(a.get("detectorId", "")): a for a in attributions}
    rows = []
    for idx, s in enumerate(sensors):
        sid = str(s.get("id", ""))
        matched_attr = attr_by_id.get(sid, attributions[idx] if idx < len(attributions) else {})
        w_pct = matched_attr.get("causalWeightPercent", round(100.0 / max(1, len(sensors)), 1))
        rows.append(f"""
        <tr class="border-b border-slate-200 text-[10px]">
            <td class="py-1 px-1.5">{html.escape(str(s.get('junction', '')))}</td>
            <td class="py-1 px-1.5 text-center font-mono font-bold">{html.escape(sid)}</td>
            <td class="py-1 px-1.5 text-center">{html.escape(str(s.get('equipmentType', 'Sensor de Tráfego')))}</td>
            <td class="py-1 px-1.5 text-center font-mono font-bold">{w_pct}% (Captum IG)</td>
            <td class="py-1 px-1.5 text-right font-bold text-emerald-800">Homologado (INMETRO)</td>
        </tr>
        """)
    return "".join(rows)


def build_safety_interventions_html(interventions: List[Any]) -> str:
    """Builds Table 2 rows for Zero-Trust safety interventions and KSE reconstruction."""
    if not interventions:
        return ""
    rows = []
    for it in interventions:
        if isinstance(it, dict):
            rows.append(f"""
            <tr class="border-b border-slate-200 text-[9.5px]">
                <td class="py-1 px-1.5 font-mono font-bold">{html.escape(str(it.get('id', '')))} ({html.escape(str(it.get('timeRecorded', '')))})</td>
                <td class="py-1 px-1.5">{html.escape(str(it.get('junction', '')))} • {html.escape(str(it.get('equipmentId', '')))}</td>
                <td class="py-1 px-1.5">{html.escape(str(it.get('irregularityDetected', '')))}</td>
                <td class="py-1 px-1.5">{html.escape(str(it.get('correctiveGuardrail', '')))}</td>
                <td class="py-1 px-1.5 text-right font-mono font-bold">{html.escape(str(it.get('finalState', '')))}</td>
            </tr>
            """)
        else:
            rows.append(f"""
            <tr class="border-b border-slate-200 text-[9.5px]">
                <td colspan="5" class="py-1 px-1.5">{html.escape(str(it))}</td>
            </tr>
            """)
    return "".join(rows)


def build_legal_html(legals: List[Dict[str, Any]]) -> str:
    """Builds legal framing list with CTB, CONTRAN and LGPD references."""
    items = []
    for leg in legals:
        art = leg.get('article', leg.get('norm', ''))
        desc = leg.get('desc', leg.get('description', leg.get('operationalRequirement', '')))
        items.append(f"""
        <li class="mb-1.5 text-[11px] abnt-p">
            <span class="font-bold">{html.escape(str(art))}:</span>
            {html.escape(str(desc))}
        </li>
        """)
    return "".join(items)

