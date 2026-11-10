# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Unit tests for nominal report generation scenarios 5 to 7.
Validates third-party feeds, physical detectors, and empty data handling.
"""

from typing import Any, Dict, List
import pytest

from src.services.traffic_report_service import TrafficReportService
from src.validation.report_validation_gate import ReportValidationGate
from src.validation.exceptions import ReportValidationError


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
# SCENARIO 5: SÓ FEEDS DE TERCEIROS (SEM RADAR / CÂMERA)
# ==============================================================================
def test_scenario_5_only_feeds():
    sensors = [
        {
            "id": "WAZE-01",
            "name": "Feed Waze Exclusivo",
            "equipmentType": "Feed de Terceiros (API Waze)",
            "measuredSpeed": "14,2 km/h",
            "saturation": "0,82",
            "canonical_source_type": "third_party_feed",
        },
        {
            "id": "TOMTOM-01",
            "name": "Feed TomTom Exclusivo",
            "equipmentType": "Feed de Terceiros (API TomTom)",
            "measuredSpeed": "12,8 km/h",
            "saturation": "0,85",
            "canonical_source_type": "third_party_feed",
        },
    ]

    service = TrafficReportService()
    res = service.build_report(override_sensors=sensors, xai_result=_create_sample_xai(["WAZE-01", "TOMTOM-01"]))

    assert res["ready"] is True
    report_data = res["report"]
    md = res["formatted_markdown"]

    assert "CONTRAN" not in md
    assert "798/2020" not in md
    assert "Detectores Físicos (Radares Doppler e Laços)" not in md
    assert "Feeds Agregados de Mobilidade" in md
    assert "Verificar em campo" in md
    assert "Ajustar tempos semafóricos prioritariamente" not in md

    ReportValidationGate.assert_valid_report(report_data, md)


# ==============================================================================
# SCENARIO 6: SÓ DETECTORES FÍSICOS (RADAR DOPPLER)
# ==============================================================================
def test_scenario_6_only_physical_detectors():
    sensors = [
        {
            "id": "RADAR-F01",
            "name": "Radar Doppler de Fiscalização 01",
            "equipmentType": "Radar de Fiscalização Metrológica",
            "purpose": "fiscalizacao",
            "is_enforcement": True,
            "measuredSpeed": "2,5 km/h",
            "saturation": "0,95",
            "canonical_source_type": "physical_radar",
        }
    ]

    service = TrafficReportService()
    res = service.build_report(override_sensors=sensors, xai_result=_create_sample_xai(["RADAR-F01"]))

    assert res["ready"] is True
    report_data = res["report"]
    md = res["formatted_markdown"]

    assert "Resolução CONTRAN nº 798/2020" in md
    assert "Feeds Agregados de Mobilidade" not in md
    assert "Detectores Físicos (Radares Doppler):" in md
    assert "Laços" not in md
    assert "Ajustar tempos semafóricos prioritariamente" in md

    ReportValidationGate.assert_valid_report(report_data, md)


# ==============================================================================
# SCENARIO 7: DADOS AUSENTES OU VAZIOS
# ==============================================================================
def test_scenario_7_missing_or_empty_data():
    service = TrafficReportService()
    res = service.build_report(override_sensors=[])

    assert res["ready"] is False
    assert res["status"] == "DATA_GENERATING"
    assert "RELATÓRIO TÉCNICO EM PROCESSAMENTO" in res["formatted_markdown"]

    with pytest.raises(ReportValidationError) as exc_info:
        ReportValidationGate.assert_valid_report({}, "")
    assert exc_info.value.violations[0].error_class == 8


# ==============================================================================
# SCENARIO 8: CORREDOR COM 4 FONTES MISTAS (CÂMERA, RADAR E FEEDS GLOBAIS)
# ==============================================================================
def test_scenario_mixed_four_sources_local_and_feeds():
    from unittest.mock import MagicMock
    from src.report.sensor_extractor import SensorTelemetryExtractor
    from src.domain.entities import SourceType

    s1 = MagicMock(id="src_1", name="Camera 01 - Rua Afonso Pena", source_type=SourceType.API, is_local=True, last_speed=24.5)
    s2 = MagicMock(id="src_2", name="Radar 01 - Avenida Dom Pedro II", source_type=SourceType.API, is_local=True, last_speed=18.0)
    s3 = MagicMock(id="src_3", name="Waze Traffic Feed", source_type=SourceType.API, is_local=False, last_speed=0.9)
    s4 = MagicMock(id="src_4", name="TomTom Traffic Flow", source_type=SourceType.API, is_local=False, last_speed=21.1)

    app_state = MagicMock()
    app_state.get_all_data_sources.return_value = [s1, s2, s3, s4]

    sensors = SensorTelemetryExtractor.extract_sensors(app_state)
    assert len(sensors) == 4
    assert sensors[0]["canonical_source_type"] == "computer_vision"
    assert sensors[0]["speedLabel"] == "Velocidade Estimada"
    assert sensors[1]["canonical_source_type"] == "physical_radar"
    assert sensors[1]["speedLabel"] == "Velocidade Aferida"
    assert sensors[2]["canonical_source_type"] == "third_party_feed"
    assert sensors[2]["speedLabel"] == "Velocidade Informada"
    assert sensors[3]["canonical_source_type"] == "third_party_feed"
    assert sensors[3]["speedLabel"] == "Velocidade Informada"

    service = TrafficReportService()
    res = service.build_report(override_sensors=sensors, xai_result=_create_sample_xai(["src_1", "src_2", "src_3", "src_4"]))
    assert res["ready"] is True
    assert res["status"] == "READY"
    ReportValidationGate.assert_valid_report(res["report"], res["formatted_markdown"])

