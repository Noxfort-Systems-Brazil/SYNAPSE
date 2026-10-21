# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
from unittest.mock import MagicMock

from src.report.traffic_kinematics import TrafficKinematicsCalculator
from src.report.sensor_extractor import SensorTelemetryExtractor
from src.report.network_summary import NetworkSummaryCalculator
from src.report.attribution_extractor import XAIAttributionExtractor
from src.report.jurist_diagnosis import JuristDiagnosisGenerator
from src.report.template_loader import TrafficReportTemplateLoader, MunicipalConfigResolver
from src.report.report_data_collector import TrafficReportDataCollector


def test_traffic_kinematics_calculator_regimes_and_metrics():
    # Forced Flow (< 10 km/h)
    forced = TrafficKinematicsCalculator.derive_sensor_kinematics(5.0)
    assert "Fluxo Forçado" in forced["saturationDegree"]
    assert "veíc/h" in forced["measuredFlow"]
    assert "%" in forced["occupancyRate"]

    # Saturated Flow (10 - 20 km/h)
    sat = TrafficKinematicsCalculator.derive_sensor_kinematics(15.0)
    assert "Fluxo Saturado" in sat["saturationDegree"]

    # Free Flow (> 35 km/h)
    free = TrafficKinematicsCalculator.derive_sensor_kinematics(45.0)
    assert "Fluxo Livre" in free["saturationDegree"]

    # Network regime classification
    fl_label, los_label = TrafficKinematicsCalculator.classify_network_regime(7.5)
    assert "Fluxo Forçado" in fl_label
    assert "Nível de Serviço F" in los_label

    fl_free, los_free = TrafficKinematicsCalculator.classify_network_regime(38.0)
    assert "Fluxo Livre" in fl_free
    assert "Nível de Serviço A / B" in los_free


def test_sensor_telemetry_extractor():
    mock_src_1 = MagicMock(id="SRC-1", name="Cruzamento 1", source_type="Doppler", last_speed=28.0)
    mock_src_2 = MagicMock(id="SRC-2", name="Cruzamento 2", source_type="Camera", last_speed=6.5)

    mock_app_state = MagicMock()
    mock_app_state.get_all_data_sources.return_value = [mock_src_1, mock_src_2]

    sensors = SensorTelemetryExtractor.extract_sensors(mock_app_state)
    assert len(sensors) == 2
    assert sensors[0]["id"] == "SRC-1"
    assert sensors[0]["operationalStatus"] == "Operação Nominal"
    assert "28.0 km/h" in sensors[0]["measuredSpeed"]

    assert sensors[1]["id"] == "SRC-2"
    assert sensors[1]["operationalStatus"] == "Alerta de Retenção Crítica"
    assert "6.5 km/h" in sensors[1]["measuredSpeed"]
    assert "Fluxo Forçado" in sensors[1]["saturationDegree"]


def test_network_summary_calculator():
    sensors = [
        {"measuredSpeed": "20.0 km/h", "measuredFlow": "1.200 veíc/h", "saturationDegree": "0,70"},
        {"measuredSpeed": "30.0 km/h", "measuredFlow": "1.400 veíc/h", "saturationDegree": "0,50"},
    ]
    summary = NetworkSummaryCalculator.compute_network_summary(sensors)
    assert summary["networkMeanSpeed"] == "25.0 km/h"
    assert summary["averageCorridorSpeed"] == "25.0 km/h"
    assert summary["monitoredJunctionsCount"] == 2
    assert summary["totalSensorsOnline"] == 2
    assert summary["totalHourlyFlow"] == "2.600 veíc/h"
    assert "0,60" in summary["globalSaturationIndex"]


def test_xai_attribution_extractor_with_captum_and_kinematic():
    sensors = [
        {"id": "DET-1", "junction": "Ponto A", "measuredSpeed": "12.0 km/h"},
        {"id": "DET-2", "junction": "Ponto B", "measuredSpeed": "42.0 km/h"},
    ]

    # Test 1: Captum neural gradients
    xai_mock = {
        "feature_names": ["DET-1 fluxo", "DET-2 velocidade"],
        "attributions": [0.65, -0.35],
    }
    attrs = XAIAttributionExtractor.extract_attributions(xai_mock, sensors)
    assert len(attrs) == 2
    assert abs(sum(a["causalWeightPercent"] for a in attrs) - 100.0) < 0.1
    assert "Positiva (+)" in attrs[0]["gradientDirection"]
    assert "Negativa (-)" in attrs[1]["gradientDirection"]

    # Test 2: Kinematic fallback (proportional to baseline deviation)
    attrs_fallback = XAIAttributionExtractor.extract_attributions(None, sensors)
    assert len(attrs_fallback) == 2
    assert abs(sum(a["causalWeightPercent"] for a in attrs_fallback) - 100.0) < 0.1
    assert attrs_fallback[0]["causalWeightPercent"] > attrs_fallback[1]["causalWeightPercent"]


def test_jurist_diagnosis_generator():
    mock_jurist = MagicMock()
    mock_jurist.generate_report.return_value = "Laudo emitido com sucesso."

    sensors = [{"id": "DET-1", "measuredSpeed": "22.0 km/h"}]
    summary = {"totalHourlyFlow": "1.500 veíc/h", "networkMeanSaturation": "0,65"}

    # With JuristAgent
    diag = JuristDiagnosisGenerator.generate_jurist_diagnosis(
        jurist_agent=mock_jurist,
        sensors=sensors,
        summary=summary,
        regime="Regime Estável",
        comparative={},
        xai_result=None,
    )
    assert "Laudo emitido com sucesso." in diag

    # Without JuristAgent (Analytical synthesis fallback)
    diag_fallback = JuristDiagnosisGenerator.generate_jurist_diagnosis(
        jurist_agent=None,
        sensors=sensors,
        summary=summary,
        regime="Regime Estável",
        comparative={},
        xai_result=None,
    )
    assert "Supervisão operacional contínua em tempo real" in diag_fallback
    assert "MARKVART™" in diag_fallback
    assert "Resolução CONTRAN nº 798/2020" in diag_fallback


def test_template_loader_and_municipal_resolver(tmp_path):
    import json
    dummy_data = {"systemVersion": "TestSys 1.0", "defaultAttribution": {"cityHall": "Prefeitura Teste"}}
    tmp_file = tmp_path / "temp_tpl.json"
    tmp_file.write_text(json.dumps(dummy_data), encoding="utf-8")

    loader = TrafficReportTemplateLoader(template_path=str(tmp_file))
    loaded = loader.load_template()
    assert loaded["systemVersion"] == "TestSys 1.0"

    cfg = MunicipalConfigResolver.resolve_municipal_config({"authorityName": "Novo Autor"}, loaded)
    assert cfg["cityHall"] == "Prefeitura Teste"
    assert cfg["authorityName"] == "Novo Autor"


def test_facade_traffic_report_data_collector_parity():
    """Validates that TrafficReportDataCollector facade transparently routes to new modular units."""
    mock_src = MagicMock(id="SRC-FACADE", name="Estação Central", source_type="Radar", last_speed=19.5)
    mock_app_state = MagicMock()
    mock_app_state.get_all_data_sources.return_value = [mock_src]

    sensors = TrafficReportDataCollector.extract_sensors(mock_app_state)
    assert len(sensors) == 1
    assert sensors[0]["id"] == "SRC-FACADE"

    summary = TrafficReportDataCollector.compute_network_summary(sensors)
    assert summary["monitoredJunctionsCount"] == 1
    assert "19.5 km/h" in summary["averageCorridorSpeed"]

    attrs = TrafficReportDataCollector.extract_attributions(None, sensors)
    assert len(attrs) == 1
    assert attrs[0]["causalWeightPercent"] == 100.0


def test_services_report_backward_compatibility_shim():
    """Validates that importing from src.services.report.report_data_collector still functions identically."""
    from src.services.report.report_data_collector import (
        TrafficReportDataCollector as ShimCollector,
        TrafficReportTemplateLoader as ShimLoader,
    )
    assert issubclass(ShimCollector, TrafficReportDataCollector) or ShimCollector is TrafficReportDataCollector
    assert issubclass(ShimLoader, TrafficReportTemplateLoader) or ShimLoader is TrafficReportTemplateLoader
