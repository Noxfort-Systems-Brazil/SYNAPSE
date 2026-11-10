# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Unit tests validating Internationalization (i18n) of the XAI Municipal Traffic Report:
- Portuguese (pt_br) standard emission
- English (en_us) localized emission
- Spanish (es_es) localized emission
- Graceful fallback for unsupported languages (e.g. de_de -> pt_br)
- DOCX exporter localization
"""

import os
from unittest.mock import MagicMock
from src.services.traffic_report_service import TrafficReportService
from src.formatters.abnt_docx_exporter import AbntDocxExporter


def _sample_sensors():
    return [
        {
            "id": "src_1",
            "name": "Av. Paulista x R. Augusta",
            "equipmentType": "Radar Doppler",
            "measuredSpeed": "22.5 km/h",
            "laneOccupancy": "35.0%",
            "flowRate": "1200 veíc/h",
            "saturationLevel": 0.65,
            "availability": 99.8,
            "is_enforcement": False,
            "processes_personal_data": False,
        },
        {
            "id": "src_2",
            "name": "Av. 23 de Maio - Km 4",
            "equipmentType": "Waze Traffic Feed",
            "measuredSpeed": "18.0 km/h",
            "laneOccupancy": "42.0%",
            "flowRate": "1450 veíc/h",
            "saturationLevel": 0.78,
            "availability": 98.5,
            "is_enforcement": False,
            "processes_personal_data": False,
        },
    ]


def _sample_xai(agent_ids):
    analyses = {}
    for aid in agent_ids:
        analyses[aid] = {
            "sorted_analysis": [
                {"name": "Velocidade Aferida (km/h)", "importance": 0.35, "description": "Velocidade"},
                {"name": "Taxa de Ocupação da Faixa (%)", "importance": 0.25, "description": "Ocupação"},
                {"name": "Grau de Saturação (x = V/c)", "importance": 0.20, "description": "Saturação"},
                {"name": "Volume de Fluxo Veicular (veíc/h)", "importance": 0.20, "description": "Volume"},
            ]
        }
    return {"analyses": analyses}


def test_report_generation_pt_br():
    sensors = _sample_sensors()
    xai = _sample_xai(["src_1", "src_2"])
    service = TrafficReportService()

    res = service.build_report(
        override_sensors=sensors,
        xai_result=xai,
        language="pt_br",
    )
    assert res["ready"] is True
    markdown = res["formatted_markdown"]

    assert "## PARTE I — SUMÁRIO EXECUTIVO" in markdown
    assert "## PARTE II — AUDITORIA PERICIAL" in markdown
    assert "## PARTE III — FICHAS TÉCNICAS E PERICIAIS" in markdown
    assert "## PARTE IV — DIRETRIZES TÉCNICAS E PARECER CONCLUSIVO" in markdown
    assert "2.2.1" in markdown


def test_report_generation_en_us():
    sensors = _sample_sensors()
    xai = _sample_xai(["src_1", "src_2"])
    service = TrafficReportService()

    res = service.build_report(
        override_sensors=sensors,
        xai_result=xai,
        language="en_US",
    )
    assert res["ready"] is True
    markdown = res["formatted_markdown"]

    assert "## PART I — EXECUTIVE SUMMARY" in markdown
    assert "## PART II — TRAFFIC ENGINEERING, IT AND XAI FORENSIC AUDIT" in markdown
    assert "## PART III — FORENSIC TECHNICAL SHEETS" in markdown
    assert "## PART IV — TECHNICAL DIRECTIVES" in markdown
    assert "2.2.1" in markdown


def test_report_generation_es_es():
    sensors = _sample_sensors()
    xai = _sample_xai(["src_1", "src_2"])
    service = TrafficReportService()

    res = service.build_report(
        override_sensors=sensors,
        xai_result=xai,
        language="es_ES",
    )
    assert res["ready"] is True
    markdown = res["formatted_markdown"]

    assert "## PARTE I — RESUMEN EJECUTIVO" in markdown
    assert "## PARTE II — AUDITORÍA PERICIAL" in markdown
    assert "## PARTE III — FICHAS TÉCNICAS PERICIALES" in markdown
    assert "## PARTE IV — DIRECTRICES TÉCNICAS" in markdown
    assert "2.2.1" in markdown


def test_report_generation_fallback_unsupported_language():
    sensors = _sample_sensors()
    xai = _sample_xai(["src_1", "src_2"])
    service = TrafficReportService()

    # Unsupported language should fall back cleanly to pt_br
    res = service.build_report(
        override_sensors=sensors,
        xai_result=xai,
        language="de_DE",
    )
    assert res["ready"] is True
    markdown = res["formatted_markdown"]

    assert "## PARTE I — SUMÁRIO EXECUTIVO" in markdown
    assert "## PARTE IV — DIRETRIZES TÉCNICAS" in markdown


def test_docx_export_localized():
    sensors = _sample_sensors()
    xai = _sample_xai(["src_1", "src_2"])
    service = TrafficReportService()

    # Build report data in en_US
    res = service.build_report(override_sensors=sensors, xai_result=xai, language="en_US")
    assert res["ready"] is True
    report_data = res["report"]

    exporter = AbntDocxExporter()
    output_path = "/tmp/test_synapse_report_en.docx"
    try:
        doc = exporter.generate(report_data, typography_options={"fontFamily": "Times New Roman", "lineSpacing": 1.5})
        assert doc is not None
        doc.save(output_path)
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 1000
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)
