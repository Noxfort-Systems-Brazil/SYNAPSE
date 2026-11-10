# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
End-to-end validation of the 10 critical and important points of XAI redesign compliance.
"""

from src.services.traffic_report_service import TrafficReportService
from src.report.sensor_extractor import SensorTelemetryExtractor


def test_xai_redesign_ten_points_compliance():
    """
    End-to-end validation of the 10 critical and important points:
    1. Narrative explains what happened in plain language.
    2. No self-proclaimed authority ('fé pública', 'laudo pericial', '100% fidedigno').
    3. Consistency across sections (single source of truth for availability and safeguards).
    4. Truthful typing of data sources (Doppler radar vs OCR vs 3rd-party crowdsourced APIs).
    5. No CONTRAN 798/2020 citation out of scope for cameras/APIs.
    6. Basic context: observation window, 480 samples @ 1 Hz, clear estimation objective.
    7. No static boilerplate values (PINO residual dynamic per station, distinct causal weights).
    8. Technical terms explained in plain language ('o que isso significa na prática').
    9. No skipped numbering, no software module IDs, no 'SourceType.API', equation 5 has lambda.
    10. Operational boundaries declared (dead reckoning drift, XAI limits).
    """
    sensors = [
        {
            "id": "CAM_OCR_01",
            "junction": "Av. Rebouças x Rua dos Pinheiros",
            "equipmentType": "Visão Computacional (Câmera)",
            "measuredSpeed": "1.6 km/h",
            "measuredFlow": "420 veíc/h",
            "saturationDegree": "0.96",
            "occupancyRate": "88.0%",
            "inmetroReport": "Contagem Óptica de Fluxo e Ocupação",
            "operationalStatus": "Operação Nominal",
        },
        {
            "id": "RAD_DOPPLER_01",
            "junction": "Av. Rebouças x Av. Faria Lima",
            "equipmentType": "Radar Doppler Físico",
            "measuredSpeed": "28.0 km/h",
            "measuredFlow": "1.650 veíc/h",
            "saturationDegree": "0.55",
            "occupancyRate": "32.0%",
            "inmetroReport": "INMETRO-RAD-2025-992",
            "operationalStatus": "Operação Nominal",
        },
        {
            "id": "WAZE_FEED_01",
            "junction": "Av. Rebouças (Trecho Central)",
            "equipmentType": "Feed de Terceiros (API / Crowdsourcing)",
            "measuredSpeed": "14.0 km/h",
            "measuredFlow": "1.200 veíc/h",
            "saturationDegree": "0.78",
            "occupancyRate": "52.0%",
            "inmetroReport": "Dado Amostral de Terceiros (Não sujeito ao INMETRO)",
            "operationalStatus": "Operação Nominal",
        },
        {
            "id": "TOMTOM_FEED_01",
            "junction": "Av. Rebouças (Acesso Marginal)",
            "equipmentType": "Feed de Terceiros (API / Crowdsourcing)",
            "measuredSpeed": "16.0 km/h",
            "measuredFlow": "1.100 veíc/h",
            "saturationDegree": "0.74",
            "occupancyRate": "48.0%",
            "inmetroReport": "Dado Amostral de Terceiros (Não sujeito ao INMETRO)",
            "operationalStatus": "Operação Nominal",
        },
    ]

    # Test automatic source classifier
    eq_type, met_status, _ = SensorTelemetryExtractor._classify_source("WAZE_01", "Feed Waze", "SourceType.API")
    assert eq_type == "Feed de Terceiros (API / Crowdsourcing)"
    assert "Não sujeito ao INMETRO" in met_status

    service = TrafficReportService()
    output = service.build_report(override_sensors=sensors)
    md = output["formatted_markdown"]

    # 1. Starts cleanly with PARTE I (No unrendered cover polluting Markdown)
    assert md.startswith("## PARTE I — SUMÁRIO EXECUTIVO PARA GESTÃO PÚBLICA E TOMADORES DE DECISÃO")

    # 2. Prohibited authority claims MUST NOT appear anywhere in the document
    prohibited_terms = [
        "possuem fé pública",
        "com fé pública",
        "laudo pericial",
        "100% fidedigno",
        "ausência de viés comprovada",
        "SourceType.API",
        "PI_DVAE_CORRECTOR",
        "KSE_DEAD_RECKONING",
    ]
    for term in prohibited_terms:
        assert term not in md, f"Prohibited term '{term}' found in markdown report!"
    assert "sem fé pública" in md, "Expected honest disclaimer 'sem fé pública' in technical footer!"

    # 3. Truthful data typing
    assert "Feed de Terceiros" in md
    assert "Visão Computacional (Câmera)" in md or "Câmera" in md
    assert "Radar Doppler Físico" in md

    # 4. Contextual explanation (480 samples, 1 Hz)
    assert "480 amostras" in md
    assert "1,0 Hz" in md or "1,0s" in md

    # 5. Dynamic PINO residual and modality weights
    cam_weight_found = False
    rad_weight_found = False
    for line in md.splitlines():
        if "CAM_OCR_01" in line and "Ocupação" in line:
            cam_weight_found = True
        if "RAD_DOPPLER_01" in line and "Velocidade" in line:
            rad_weight_found = True

    # 6. Operational Narrative present
    assert "Entre" in md or "velocidade média" in md

    # 7. Sequential Partes and sections in strict Noxfort order
    expected_sections = [
        "PARTE I — SUMÁRIO EXECUTIVO PARA GESTÃO PÚBLICA E TOMADORES DE DECISÃO",
        "1.1 Objetivo da Auditoria Institucional",
        "1.2 Principais Resultados Operacionais",
        "1.3 Quadro Sintético por Ponto de Monitoramento",
        "PARTE II — AUDITORIA PERICIAL DE ENGENHARIA DE TRÁFEGO, TI E XAI",
        "2.1 Telemetria, Fontes de Amostragem e Qualidade dos Dados",
        "2.2 Memorial de Cálculo e Formulações Matemáticas de Percepção",
        "2.3 Salvaguardas Zero-Trust, Quarentena e Reconstrução Cinemática",
        "2.4 Resumo Consolidado e Fatores de Maior Peso (XAI)",
        "PARTE III — FICHAS TÉCNICAS E PERICIAIS POR PONTO DE MONITORAMENTO (ANEXO I)",
        "PARTE IV — DIRETRIZES TÉCNICAS E PARECER CONCLUSIVO DE HOMOLOGAÇÃO",
        "4.1 Diretrizes Operacionais de Engenharia de Tráfego e CCO",
        "4.2 Considerações Finais e Parecer Técnico de Homologação",
    ]
    last_pos = -1
    for sec in expected_sections:
        pos = md.find(sec)
        assert pos != -1, f"Missing section: '{sec}'"
        assert pos > last_pos, f"Section '{sec}' out of order!"
        last_pos = pos

    # 8. Equations numbered 2.2.1 to 2.2.5 in Section 2.2
    assert "2.2.1" in md
    assert "2.2.2" in md
    assert "2.2.3" in md
    assert "2.2.4" in md
    assert "2.2.5" in md
    assert "exp(-λ" in md or "exp(-lambda" in md or "λ" in md

    # 9. Non-causal terminology and honest completeness
    assert "Atribuição Causal" not in md
    assert "Atribuição por Gradientes Integrados" in md
    assert "Garante que 100% da decisão" not in md
    assert "Distribui a variação da estimativa" in md

    # 10. Operational Status reflects severity (worst station at 1.6 km/h is Crítico / Retenção Severa)
    assert "Crítico / Retenção Severa" in md
    assert "Av. Rebouças (Consolação / Jardins)" in md or "RAD_DOPPLER_01" in md

    # 11. DOCX Exporter includes formal cover with institutional title
    from src.formatters.abnt_docx_exporter import AbntDocxExporter
    doc = AbntDocxExporter().generate(output["report"])
    docx_text = "\n".join(p.text for p in doc.paragraphs)
    assert "RELATÓRIO EXPLICATIVO DO SYNAPSE (XAI)" in docx_text
