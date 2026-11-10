# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Unit tests for nominal report generation scenarios 1 to 4.
Validates free-flow, congested corridors, mixed bottlenecks, and safety intervention accounting.
"""

from typing import Any, Dict, List

from src.services.traffic_report_service import TrafficReportService
from src.report.traffic_regime_classifier import TrafficRegimeClassifier
from src.validation.report_validation_gate import ReportValidationGate


def _create_sample_xai(agent_ids: List[str]) -> Dict[str, Any]:
    analyses = {}
    for aid in agent_ids:
        analyses[aid] = {
            "top_features": [
                {"feature": "Velocidade", "importance": 0.40},
                {"feature": "Densidade", "importance": 0.35},
                {"feature": "Ocupação", "importance": 0.15},
                {"feature": "Volume", "importance": 0.10},
            ]
        }
    return {"analyses": analyses}


# ==============================================================================
# SCENARIO 1: TUDO FLUIDO (FREE FLOW)
# ==============================================================================
def test_scenario_1_all_fluid():
    sensors = [
        {
            "id": "DET-S1-01",
            "name": "Estação Norte 01",
            "equipmentType": "Radar Doppler",
            "measuredSpeed": "55,0 km/h",
            "saturation": "0,25",
            "occupancyRate": "12,0%",
            "volumePerHour": "450",
            "canonical_source_type": "physical_radar",
        },
        {
            "id": "DET-S1-02",
            "name": "Estação Norte 02",
            "equipmentType": "Radar Doppler",
            "measuredSpeed": "52,0 km/h",
            "saturation": "0,28",
            "occupancyRate": "14,0%",
            "volumePerHour": "510",
            "canonical_source_type": "physical_radar",
        },
    ]

    service = TrafficReportService()
    res = service.build_report(override_sensors=sensors, xai_result=_create_sample_xai(["DET-S1-01", "DET-S1-02"]))

    assert res["ready"] is True
    assert res["status"] == "READY"
    report_data = res["report"]
    md = res["formatted_markdown"]

    corridor_info = TrafficRegimeClassifier.classify_corridor(sensors)
    assert corridor_info["corridor_tier"] == 1
    assert "Livre / Fluido" in corridor_info["corridor_regime"]

    assert "Livre / Fluido" in md
    assert "Fluxo operando dentro dos parâmetros nominais" in md

    ReportValidationGate.assert_valid_report(report_data, md)


# ==============================================================================
# SCENARIO 2: TUDO CONGESTIONADO (FORCED FLOW / SEVERE RETENTION)
# ==============================================================================
def test_scenario_2_all_congested():
    sensors = [
        {
            "id": "DET-S2-01",
            "name": "Estação Sul 01",
            "equipmentType": "Radar Doppler",
            "measuredSpeed": "3,2 km/h",
            "saturation": "0,95",
            "occupancyRate": "88,0%",
            "volumePerHour": "180",
            "canonical_source_type": "physical_radar",
        },
        {
            "id": "DET-S2-02",
            "name": "Estação Sul 02 (Gargalo)",
            "equipmentType": "Radar Doppler",
            "measuredSpeed": "1,1 km/h",
            "saturation": "0,99",
            "occupancyRate": "96,0%",
            "volumePerHour": "120",
            "canonical_source_type": "physical_radar",
        },
    ]

    service = TrafficReportService()
    res = service.build_report(override_sensors=sensors, xai_result=_create_sample_xai(["DET-S2-01", "DET-S2-02"]))

    assert res["ready"] is True
    report_data = res["report"]
    md = res["formatted_markdown"]

    corridor_info = TrafficRegimeClassifier.classify_corridor(sensors)
    assert corridor_info["corridor_tier"] == 4
    assert "Crítico / Retenção Severa" in corridor_info["corridor_regime"]
    assert "Pontos em regime crítico (2 de 2)" in md

    ReportValidationGate.assert_valid_report(report_data, md)


# ==============================================================================
# SCENARIO 3: CORREDOR MISTO (SISTEMA DEVE PRIORIZAR O PIOR PONTO)
# ==============================================================================
def test_scenario_3_mixed_corridor():
    sensors = [
        {
            "id": "DET-M-01",
            "name": "Entrada Fluida",
            "equipmentType": "Radar Doppler",
            "measuredSpeed": "48,0 km/h",
            "saturation": "0,30",
            "canonical_source_type": "physical_radar",
        },
        {
            "id": "DET-M-02",
            "name": "Gargalo Severo",
            "equipmentType": "Radar Doppler",
            "measuredSpeed": "0,9 km/h",
            "saturation": "0,98",
            "canonical_source_type": "physical_radar",
        },
    ]

    service = TrafficReportService()
    res = service.build_report(override_sensors=sensors, xai_result=_create_sample_xai(["DET-M-01", "DET-M-02"]))

    assert res["ready"] is True
    report_data = res["report"]
    md = res["formatted_markdown"]

    assert "Gargalo Severo" in md
    assert "0,9 km/h" in md
    assert "Pontos em regime crítico (1 de 2)" in md

    ReportValidationGate.assert_valid_report(report_data, md)


# ==============================================================================
# SCENARIO 4A: SEM EVENTOS DE SEGURANÇA (100% DISPONIBILIDADE)
# ==============================================================================
def test_scenario_4a_no_safety_events():
    sensors = [
        {
            "id": "RADAR-01",
            "name": "Radar Nominal",
            "equipmentType": "Radar Doppler",
            "measuredSpeed": "40,0 km/h",
            "saturation": "0,40",
            "canonical_source_type": "physical_radar",
        }
    ]

    service = TrafficReportService()
    res = service.build_report(
        override_sensors=sensors,
        override_safety_interventions=[],
        xai_result=_create_sample_xai(["RADAR-01"]),
    )

    assert res["ready"] is True
    report_data = res["report"]
    md = res["formatted_markdown"]

    assert "100,0%" in md
    assert "Leituras anômalas em quarentena: **0**" in md or "Sem anomalias" in md

    ReportValidationGate.assert_valid_report(report_data, md)


# ==============================================================================
# SCENARIO 4B: COM EVENTOS DE SEGURANÇA (QUARENTENA, PI-DVAE, DEAD RECKONING)
# ==============================================================================
def test_scenario_4b_with_safety_events():
    sensors = [
        {
            "id": "RADAR-01",
            "name": "Radar com Incidentes",
            "equipmentType": "Radar Doppler",
            "measuredSpeed": "35,0 km/h",
            "saturation": "0,45",
            "canonical_source_type": "physical_radar",
        }
    ]

    safety_interventions = [
        {
            "id": "EVT-01",
            "equipmentId": "RADAR-01",
            "junction": "Cruzamento Principal",
            "irregularityDetected": "Discrepância de 1 leitura em quarentena",
            "correctiveGuardrail": "QUARENTENA_TEMPORAL",
            "finalState": "QUARENTENA_CONFIRMADA",
        },
        {
            "id": "EVT-02",
            "equipmentId": "RADAR-01",
            "junction": "Cruzamento Principal",
            "irregularityDetected": "Ruído de alta frequência",
            "correctiveGuardrail": "PI-DVAE",
            "finalState": "FILTRADO_PI_DVAE",
        },
        {
            "id": "EVT-03",
            "equipmentId": "RADAR-01",
            "junction": "Cruzamento Principal",
            "irregularityDetected": "Omissão de telemetria por 3 ciclos",
            "correctiveGuardrail": "KSE_DEAD_RECKONING",
            "finalState": "ESTIMATIVA_CINEMÁTICA",
        },
    ]

    service = TrafficReportService()
    res = service.build_report(
        override_sensors=sensors,
        override_safety_interventions=safety_interventions,
        xai_result=_create_sample_xai(["RADAR-01"]),
    )

    assert res["ready"] is True
    report_data = res["report"]
    md = res["formatted_markdown"]

    assert "96,7%" in md
    assert "3 ciclos sob projeção temporária" in md
    assert "1 leitura atípica em quarentena" in md

    ReportValidationGate.assert_valid_report(report_data, md)
