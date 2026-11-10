# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Unit tests validating the 8 final refinements of the XAI Municipal Traffic Report:
1. Equations A.3 and A.5 syntax, greek symbols, and no stray braces.
2. Section 4 empty table replacement when no safeguards are triggered.
3. Section 1.2 zero safeguards summary ("Nenhuma salvaguarda foi acionada.").
4. CONTRAN 798/2020 omitted unless equipment has enforcement purpose.
5. LGPD Art. 20 omitted without personal data and label unified to "Visão Computacional (Câmera)".
6. Derived variable markers preserved in Table 1.3, Section 3 disclaimer, and saturation.
7. Hourly flow text, no "Laços" when absent, and Decimal ROUND_HALF_UP rounding.
8. Authentic differentiation of telemetry across monitoring stations.
"""

from unittest.mock import MagicMock
from src.services.traffic_report_service import TrafficReportService
from src.validation.report_validation_gate import ReportValidationGate
from src.formatters.report_number_formatter import ReportNumberFormatter
from src.domain.entities import SourceType
from src.report.sensor_extractor import SensorTelemetryExtractor
from src.context.station_attribution_builder import StationAttributionBuilder


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


def test_item_1_equations_and_lint():
    import json
    with open("config/templates/xai/xai_equations.json", "r", encoding="utf-8") as f:
        eqs = json.load(f)["pt_br"]

    assert r"\sqrt{d_{\text{model}}}" in eqs["eq3_formula"]
    assert "e^{-\\lambda \\Delta t}" in eqs["eq5_formula"]
    assert "{" not in eqs["eq5_formula"].split("a_{t-1}")[0] or "a t-1}" not in eqs["eq5_formula"]
    assert "{t-1}}" not in eqs["eq5_formula"]


def test_item_2_section_4_empty_safeguards():
    sensors = [
        {"id": "RAD_01", "name": "Radar Test", "equipmentType": "Radar Doppler", "measuredSpeed": "32.0 km/h", "saturation": "0.55", "canonical_source_type": "physical_radar"}
    ]
    service = TrafficReportService()
    res = service.build_report(override_sensors=sensors, override_safety_interventions=[], xai_result=_sample_xai(["RAD_01"]))

    assert res["ready"] is True
    md = res["formatted_markdown"]
    assert "Nenhuma salvaguarda foi acionada no período analisado." in md
    assert "| Registro ID |" not in md


def test_item_3_section_1_2_zero_safeguards_summary():
    sensors = [
        {"id": "RAD_01", "name": "Radar Test", "equipmentType": "Radar Doppler", "measuredSpeed": "32.0 km/h", "saturation": "0.55", "canonical_source_type": "physical_radar"}
    ]
    service = TrafficReportService()
    res = service.build_report(override_sensors=sensors, override_safety_interventions=[], xai_result=_sample_xai(["RAD_01"]))

    assert res["ready"] is True
    md = res["formatted_markdown"]
    assert "Salvaguardas Operacionais Aplicadas:** Nenhuma salvaguarda foi acionada." in md
    assert "0 leituras atípicas em quarentena" not in md


def test_item_4_contran_798_omitted_when_monitoring():
    # 1. Monitoring radar (not enforcement) -> CONTRAN 798 must NOT appear
    sensors_mon = [
        {"id": "RAD_01", "name": "Radar de Monitoramento", "equipmentType": "Radar Doppler de Monitoramento", "measuredSpeed": "22.0 km/h", "saturation": "0.65", "canonical_source_type": "physical_radar"}
    ]
    service = TrafficReportService()
    res_mon = service.build_report(override_sensors=sensors_mon, xai_result=_sample_xai(["RAD_01"]))
    assert res_mon["ready"] is True
    assert "798/2020" not in res_mon["formatted_markdown"]

    # 2. Enforcement radar -> CONTRAN 798 legitimately appears
    sensors_enf = [
        {"id": "RAD_02", "name": "Radar de Fiscalização", "equipmentType": "Radar de Fiscalização", "is_enforcement": True, "purpose": "fiscalizacao", "measuredSpeed": "22.0 km/h", "saturation": "0.65", "canonical_source_type": "physical_radar"}
    ]
    res_enf = service.build_report(override_sensors=sensors_enf, xai_result=_sample_xai(["RAD_02"]))
    assert res_enf["ready"] is True
    assert "Resolução CONTRAN nº 798/2020" in res_enf["formatted_markdown"]


def test_item_5_lgpd_art_20_and_camera_label_unified():
    sensors = [
        {"id": "CAM_01", "name": "Câmera de Fluxo", "equipmentType": "Visão Computacional (Câmera)", "measuredSpeed": "28.0 km/h", "saturation": "0.60", "canonical_source_type": "computer_vision"}
    ]
    service = TrafficReportService()
    res = service.build_report(override_sensors=sensors, xai_result=_sample_xai(["CAM_01"]))
    assert res["ready"] is True
    md = res["formatted_markdown"]

    assert "LGPD" not in md
    assert "13.709" not in md
    assert "Visão Computacional (Câmera)" in md
    assert "Câmeras OCR" not in md


def test_item_6_derived_variables_and_table_1_3_and_section_3():
    sensors = [
        {
            "id": "WAZE_01",
            "name": "Feed Waze",
            "equipmentType": "Feed de Terceiros (API Waze)",
            "measuredSpeed": "14.0 km/h",
            "occupancyRate": "85,0%",
            "saturation": "0.80",
            "canonical_source_type": "third_party_feed",
        }
    ]
    service = TrafficReportService()
    res = service.build_report(override_sensors=sensors)
    assert res["ready"] is True
    md = res["formatted_markdown"]

    assert "Taxa de Ocupação da Faixa [Derivado por Modelo]" in md
    assert "Grau de Saturação (x = V/c) [Derivado por Modelo]" in md
    assert "As grandezas de Ocupação, Volume e Grau de Saturação identificadas com **[Derivado por Modelo]**" in md


def test_item_7_vehicle_flow_description_no_loops_and_half_up_rounding():
    # 1. Rounding half-up: 0.2945 -> 29,5%
    pct_from_ratio = ReportNumberFormatter.format_percent(0.2945, decimal_places=1, is_ratio=True)
    assert pct_from_ratio == "29,5%"
    pct_from_float = ReportNumberFormatter.format_percent(29.45, decimal_places=1, is_ratio=False)
    assert pct_from_float == "29,5%"

    # 2. No loops -> "Laços" must not appear in Section 2
    sensors = [
        {"id": "RAD_01", "name": "Radar Test", "equipmentType": "Radar Doppler", "measuredSpeed": "32.0 km/h", "saturation": "0.55", "canonical_source_type": "physical_radar"}
    ]
    service = TrafficReportService()
    res = service.build_report(override_sensors=sensors, xai_result=_sample_xai(["RAD_01"]))
    assert res["ready"] is True
    assert "Laços" not in res["formatted_markdown"]


def test_item_8_telemetry_differentiated_between_stations():
    s1 = MagicMock(id="src_1", name="Camera 01 - Rua Afonso Pena", source_type=SourceType.API, is_local=True, last_speed=24.5)
    s2 = MagicMock(id="src_2", name="Radar 01 - Avenida Dom Pedro II", source_type=SourceType.API, is_local=True, last_speed=18.0)
    app_state = MagicMock()
    app_state.get_all_data_sources.return_value = [s1, s2]

    sensors = SensorTelemetryExtractor.extract_sensors(app_state)
    assert len(sensors) == 2
    assert sensors[0]["measuredSpeed"] == "24.5 km/h"
    assert sensors[1]["measuredSpeed"] == "18.0 km/h"
    assert sensors[0]["occupancyRate"] != sensors[1]["occupancyRate"]
    assert sensors[0]["saturationDegree"] != sensors[1]["saturationDegree"]
