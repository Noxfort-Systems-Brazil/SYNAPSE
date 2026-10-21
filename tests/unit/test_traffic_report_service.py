# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

import pytest
from unittest.mock import MagicMock
from src.services.traffic_report_service import TrafficReportService
from src.handlers.system_handler import SystemCommandHandler
from src.ipc.ipc_protocol import IpcMessage


def _create_mock_sensors():
    return [
        {
            "id": "DET-REAL-01",
            "junction": "Av. Paulista x R. da Consolação",
            "equipmentType": "Radar Doppler",
            "measuredSpeed": "22.5 km/h",
            "measuredFlow": "1.420 veíc/h",
            "saturationDegree": "0,72",
            "occupancyRate": "64,0%",
            "inmetroReport": "INMETRO 9942/2025",
            "operationalStatus": "Operação Nominal",
        },
        {
            "id": "DET-REAL-02",
            "junction": "Av. Paulista x Al. Campinas",
            "equipmentType": "Laço Indutivo Virtual (Câmera)",
            "measuredSpeed": "18.0 km/h",
            "measuredFlow": "1.350 veíc/h",
            "saturationDegree": "0,78",
            "occupancyRate": "68,0%",
            "inmetroReport": "INMETRO 9943/2025",
            "operationalStatus": "Operação Nominal",
        },
    ]


def test_traffic_report_service_lock_guard_when_no_sensors():
    """Lock Guard: verifies that without active telemetry, report generation is halted."""
    service = TrafficReportService()
    ready, status, msg = service.is_data_ready()
    assert ready is False
    assert status == "DATA_GENERATING"
    assert "estão sendo gerados" in msg

    output = service.build_report()
    assert output["ready"] is False
    assert output["status"] == "DATA_GENERATING"
    assert output["report"] is None
    assert "LAUDO OFICIAL EM PROCESSAMENTO" in output["formatted_markdown"]


def test_traffic_report_service_build_with_real_sensors():
    """Generates authentic report when telemetry sensors are active."""
    mock_source = MagicMock()
    mock_source.id = "DET-MOCK-01"
    mock_source.name = "Estação Sé"
    mock_source.source_type = "Radar Doppler"
    mock_source.last_speed = 24.5

    mock_app_state = MagicMock()
    mock_app_state.get_all_data_sources.return_value = [mock_source]

    service = TrafficReportService(app_state=mock_app_state)
    ready, status, _ = service.is_data_ready()
    assert ready is True

    output = service.build_report()
    assert output["ready"] is True
    report = output["report"]

    assert report["protocol"].startswith("RELATORIO-TRAFEGO-2026-")
    assert report["processNumber"].startswith("PA-SMT-2026/")
    assert report["cityHall"] == "PREFEITURA DO MUNICÍPIO DE SÃO PAULO"
    assert len(report["sensors"]) == 1
    assert report["sensors"][0]["id"] == "DET-MOCK-01"
    assert "24.5 km/h" in report["sensors"][0]["measuredSpeed"]

    # Observed diagnosis is dynamically computed from live telemetry
    assert "MARKVART™ processou 1 detectores ativos" in report["observedTrafficDiagnosis"]
    assert "24.5 km/h" in report["observedTrafficDiagnosis"]

    # Markdown output verification
    md = output["formatted_markdown"]
    assert report["protocol"] in md
    assert "ABNT NBR 10719" in md
    assert "Código de Trânsito Brasileiro" in md


def test_traffic_report_service_custom_municipal_config():
    service = TrafficReportService()
    custom_cfg = {
        "cityHall": "PREFEITURA DE CURITIBA",
        "department": "URBS - URBANIZAÇÃO DE CURITIBA S.A.",
        "authorityName": "Engenheiro Chefe de Tráfego",
        "authorityRole": "Superintendente de Trânsito",
        "registrationNumber": "CREA-PR 99281",
        "processPrefix": "PA-URBS-2026/",
    }
    output = service.build_report(
        municipal_config=custom_cfg,
        override_sensors=_create_mock_sensors(),
    )
    assert output["ready"] is True
    report = output["report"]

    assert report["cityHall"] == "PREFEITURA DE CURITIBA"
    assert report["department"] == "URBS - URBANIZAÇÃO DE CURITIBA S.A."
    assert report["authorityName"] == "Engenheiro Chefe de Tráfego"
    assert report["processNumber"].startswith("PA-URBS-2026/")


def test_report_handler_lock_guard_and_generation_ipc():
    from src.handlers.report_handler import ReportCommandHandler
    mock_controller = MagicMock()
    mock_controller.app_state = MagicMock()

    # Step 1: No sensors -> Lock Guard active (ready=False)
    mock_controller.app_state.get_all_data_sources.return_value = []
    handler = ReportCommandHandler(controller=mock_controller)

    msg = IpcMessage(
        id="req_lock",
        action="generate_official_report",
        payload={"municipal_config": {"authorityName": "Auditor Teste"}},
    )
    resp = handler.handle_generate_official_report(msg)
    assert resp["success"] is False
    assert resp["ready"] is False
    assert resp["status"] == "DATA_GENERATING"

    # Step 2: Sensors populated -> Report generated successfully (ready=True)
    mock_source = MagicMock(id="DET-01", name="Detector 1", source_type="Radar", last_speed=20.0)
    mock_controller.app_state.get_all_data_sources.return_value = [mock_source]

    resp2 = handler.handle_generate_official_report(msg)
    assert resp2["success"] is True
    assert resp2["ready"] is True
    assert "report" in resp2
    assert resp2["report"]["authorityName"] == "Auditor Teste"


def test_traffic_report_service_interfaces():
    from src.interfaces.reports import ITrafficReportService, IReportFormatter
    from src.formatters.abnt_markdown_formatter import AbntMarkdownReportFormatter

    service = TrafficReportService()
    formatter = AbntMarkdownReportFormatter()
    assert isinstance(service, ITrafficReportService)
    assert isinstance(formatter, IReportFormatter)


def test_traffic_report_service_custom_formatter_injection():
    class DummyHtmlFormatter:
        def format(self, report_data):
            return f"<html><body><h1>Protocol: {report_data['protocol']}</h1></body></html>"

    service = TrafficReportService(formatter=DummyHtmlFormatter())
    output = service.build_report(override_sensors=_create_mock_sensors())
    assert output["ready"] is True
    assert output["formatted_markdown"].startswith("<html><body><h1>Protocol: RELATORIO-TRAFEGO-2026-")


def test_traffic_report_service_custom_template(tmp_path):
    import json

    custom_template = {
        "systemVersion": "SYNAPSE Custom v9.9",
        "auditObjective": "Auditoria Experimental Personalizada.",
        "defaultAttribution": {
            "cityHall": "PREFEITURA DE FLORIANÓPOLIS",
            "department": "IPUF - INSTITUTO DE PLANEJAMENTO URBANO",
            "authorityName": "Auditor Sênior",
            "authorityRole": "Engenheiro de Tráfego",
            "registrationNumber": "CREA-SC 12345",
            "processPrefix": "PA-IPUF-2026/",
        },
        "location": {"city": "Florianópolis, SC", "corridor": "Av. Beira-Mar Norte"},
        "safetyInterventions": ["Intervenção Teste A"],
        "quesitos": [
            {
                "id": "Q-CUSTOM-01",
                "question": "Conformidade semafórica?",
                "referenceRule": "Portaria 01/2026",
                "technicalJustification": "Conforme regras.",
                "answer": "SIM",
            }
        ],
        "legalFraming": [
            {"article": "Art. 1º", "description": "Norma", "technicalEvidence": "Telemetria."}
        ],
    }

    template_file = tmp_path / "custom_template.json"
    template_file.write_text(json.dumps(custom_template), encoding="utf-8")

    service = TrafficReportService(template_path=str(template_file))
    output = service.build_report(override_sensors=_create_mock_sensors())
    report = output["report"]

    assert report["system"] == "SYNAPSE Custom v9.9"
    assert report["auditObjective"] == "Auditoria Experimental Personalizada."
    assert report["cityHall"] == "PREFEITURA DE FLORIANÓPOLIS"
    assert len(report["quesitos"]) == 1


def test_traffic_report_service_with_jurist_agent():
    mock_jurist = MagicMock()
    mock_jurist.generate_report.return_value = (
        "Parecer Técnico Pericial SLM: Telemetria de sensores auditada e em estrita conformidade com o CTB Art. 24 e Resolução CONTRAN nº 798/2020."
    )
    service = TrafficReportService(jurist_agent=mock_jurist)
    output = service.build_report(override_sensors=_create_mock_sensors())
    assert output["ready"] is True
    report = output["report"]
    assert "Parecer Técnico Pericial SLM" in report["observedTrafficDiagnosis"]
    assert mock_jurist.generate_report.called
    call_kwargs = mock_jurist.generate_report.call_args[1]
    assert call_kwargs.get("target") == "jurist_official_report"
    assert call_kwargs.get("auto_unload") is True
    assert "inmetroCalibrationStatus" in call_kwargs.get("tensor_data", {})


def test_network_summary_and_xai_consistency_across_sections():
    """Verifies that Executive Summary (1.2), Diagnosis (2.1), and Sensor Table (3.1) share identical real metrics."""
    mock_sources = []
    for sid, name, stype, spd in [
        ("src_1", "Camera", "Camera OCR", 1.0),
        ("src_2", "Loop", "Laço Indutivo", 1.0),
        ("api_global_qt9ww", "Waze", "API Global", 3.1),
        ("api_global_jfo4p", "Tom Tom", "API Global", 21.1),
    ]:
        m = MagicMock()
        m.id = sid
        m.name = name
        m.source_type = stype
        m.last_speed = spd
        m.last_flow = None
        m.last_occupancy = None
        m.last_saturation = None
        mock_sources.append(m)

    mock_app_state = MagicMock()
    mock_app_state.get_all_data_sources.return_value = mock_sources

    service = TrafficReportService(app_state=mock_app_state)
    output = service.build_report()
    report = output["report"]
    net = report["networkSummary"]

    # Real mean speed: (1.0 + 1.0 + 3.1 + 21.1) / 4 = 6.55 -> 6.6 km/h
    assert net["networkMeanSpeed"] == "6.6 km/h"
    assert net["averageCorridorSpeed"] == "6.6 km/h"
    assert net["monitoredJunctionsCount"] == 4
    assert net["totalSensorsOnline"] == 4
    assert "Fluxo Forçado" in net["flowStateLabel"]

    # Sensor kinematics should not be identical static strings across 1.0 km/h and 21.1 km/h
    s_slow = report["sensors"][0]
    s_fast = report["sensors"][3]
    assert s_slow["occupancyRate"] != s_fast["occupancyRate"]
    assert "Fluxo Forçado" in s_slow["saturationDegree"]
    assert "Fluxo Estável" in s_fast["saturationDegree"]

    # XAI attributions should sum to 100% and differentiate weights based on kinematic deviation
    attrs = report["attributions"]
    assert len(attrs) == 4
    weights = [a["causalWeightPercent"] for a in attrs]
    assert abs(sum(weights) - 100.0) < 0.2
    assert len(set(weights)) > 1  # Not all flat 25%


def test_slm_sanitizer_data_payload_and_truncation():
    """Verifies that leaked DATA_PAYLOAD tokens and mid-sentence truncations are cleaned."""
    from src.slm.output_sanitizer import SLMOutputSanitizer

    leaked_and_truncated = (
        "O sistema SYNAPSE emite o parecer técnico-jurídico abaixo, fundamentado estritamente "
        "nos dados fornecidos no DATA_PAYLOAD e nas normas aplicáveis ao CTB. "
        "A validação metrológica demonstra precisão suficiente para o atuador downstream."
        "A coerência física da fusão multimodal é confirmada pela consistência dos parâmetros, "
        "mas a aplicação do Axioma da Completude dos Gradientes Integrados"
    )
    cleaned = SLMOutputSanitizer.sanitize(leaked_and_truncated)
    assert "DATA_PAYLOAD" not in cleaned
    assert "nos registros metrológicos auditados" in cleaned
    assert "downstream. A" in cleaned or cleaned.endswith("downstream.")
    assert cleaned.endswith(".")



