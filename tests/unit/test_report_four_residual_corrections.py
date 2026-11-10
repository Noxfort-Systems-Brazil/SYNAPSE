# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Unit tests for the 4 residual adjustments:
1. Canonical equations block (A.3 with sqrt, A.5 with lambda and no broken braces) + EquationConsistencyRule.
2. 100% +/- 0.1 rounding note on Annex I station explainability sheets.
3. Heterogeneous fallback kinematics (camera vs radar non-colliding speeds).
4. CTB legal paraphrases (Art. 1 § 2 without 'prioritário' and Art. 24 covering II and III).
"""

import pytest
from unittest.mock import MagicMock
from src.xai.canonical_equations import CanonicalReportEquations
from src.formatters.math_cleaner import clean_latex_math
from src.validation.equation_consistency_rule import EquationConsistencyRule
from src.xai.report_annex_cards_renderer import ReportAnnexCardsRenderer
from src.report.sensor_extractor import SensorTelemetryExtractor
from src.formatters.abnt_markdown_formatter import AbntMarkdownReportFormatter


def test_item_1_canonical_equations_syntax_and_cleaning():
    """Validates that Equation 3 has square root, Equation 5 has lambda and clean braces in math_cleaner."""
    eqs = {e["tag"]: e for e in CanonicalReportEquations.EQUATIONS}
    assert "2.2.3" in eqs or "A.3" in eqs
    assert "2.2.5" in eqs or "A.5" in eqs

    eq3 = eqs.get("2.2.3") or eqs["A.3"]
    eq5 = eqs.get("2.2.5") or eqs["A.5"]

    # Formula checks
    assert r"\sqrt{d_{\text{model}}}" in eq3["formula"]
    assert r"e^{-\lambda \Delta t}" in eq5["formula"]
    assert "a t-1}" not in eq5["formula"]

    # math_cleaner output checks
    cleaned_a3 = clean_latex_math(eq3["formula"])
    assert "√(d_model)" in cleaned_a3 or "√" in cleaned_a3
    assert "d_model" in cleaned_a3

    cleaned_a5 = clean_latex_math(eq5["formula"])
    assert "λ" in cleaned_a5
    assert "Δ t" in cleaned_a5
    assert "{" not in cleaned_a5 and "}" not in cleaned_a5


def test_item_1_equation_consistency_rule_blocking():
    """Validates that EquationConsistencyRule catches missing greek symbols and missing sqrt."""
    rule = EquationConsistencyRule()

    # Valid canonical equations markdown
    valid_md = "\n\n".join(
        f"{e['title']}\n{e['desc']}\n{e['formula']}\n{e['params']}"
        for e in CanonicalReportEquations.EQUATIONS
    )
    violations = rule.validate_post(markdown_text=valid_md, report_data={})
    assert len(violations) == 0

    # Corrupt A.5 by removing lambda
    corrupted_a5 = valid_md.replace(r"e^{-\lambda \Delta t}", r"e^{-\Delta t}")
    v_a5 = rule.validate_post(markdown_text=corrupted_a5, report_data={})
    assert any("Decaimento Exponencial Ausente" in v.title or "Símbolo Grego Definido Ausente" in v.title for v in v_a5)

    # Corrupt A.3 by removing sqrt
    corrupted_a3 = valid_md.replace(r"\sqrt{d_{\text{model}}}", r"d_{\text{model}}")
    v_a3 = rule.validate_post(markdown_text=corrupted_a3, report_data={})
    assert any("Fator de Escala Ausente" in v.title for v in v_a3)


def test_item_2_annex_cards_rounding_note():
    """Validates that Annex I station cards include the rounding note."""
    renderer = ReportAnnexCardsRenderer(templates={})
    lines = []
    block = {
        "title_key": "anexo_title",
        "card_header": "agent_card_header",
        "card_intro": "agent_card_intro",
        "card_item": "agent_card_item",
    }
    context = {
        "agent_ids": ["RAD_01", "CAM_01"],
        "sensors_lookup": {
            "RAD_01": {"junction": "Av. Paulista", "equipmentType": "Radar Doppler"},
            "CAM_01": {"junction": "Rua Augusta", "equipmentType": "Câmera OCR"},
        },
        "metrics_by_agent": {
            "RAD_01": {
                "has_data": True,
                "items": [
                    {"name": "Velocidade", "pct_str": "45,5%", "importance": 0.455, "description": "Velocidade"},
                    {"name": "Ocupação", "pct_str": "54,6%", "importance": 0.546, "description": "Ocupação"},
                ],
            },
            "CAM_01": {
                "has_data": True,
                "items": [
                    {"name": "Velocidade", "pct_str": "35,1%", "importance": 0.351, "description": "Velocidade"},
                    {"name": "Ocupação", "pct_str": "65,0%", "importance": 0.650, "description": "Ocupação"},
                ],
            },
        },
        "guardian_stats": {},
    }

    renderer.render(lines, block, context)
    rendered_text = "\n".join(lines)

    expected_note = "Os percentuais podem somar 100% ± 0,1 por arredondamento."
    assert expected_note in rendered_text
    assert rendered_text.count(expected_note) == 1


def test_item_3_heterogeneous_fallback_speeds():
    """Validates that camera and radar fallback speeds and kinematics do not collide."""
    app_state = MagicMock()
    src_cam = MagicMock(id="src_1", name="Rua Augusta", source_type="Câmera OCR", is_local=True, last_speed=None, latest_value=None)
    src_rad = MagicMock(id="src_2", name="Av. Paulista", source_type="Radar Doppler", is_local=True, last_speed=None, latest_value=None)
    app_state.get_all_data_sources.return_value = [src_cam, src_rad]

    sensors = SensorTelemetryExtractor.extract_sensors(app_state)
    assert len(sensors) == 2

    cam_sensor = sensors[0]
    rad_sensor = sensors[1]

    assert cam_sensor["measuredSpeed"] != rad_sensor["measuredSpeed"]
    assert cam_sensor["occupancyRate"] != rad_sensor["occupancyRate"]
    assert cam_sensor["saturationDegree"] != rad_sensor["saturationDegree"]


def test_item_4_ctb_legal_paraphrases_in_report():
    """Validates that CTB Art. 1 § 2 removes 'prioritário' and Art. 24 describes incisos II and III."""
    sensors = [
        {
            "id": "RAD_01",
            "junction": "Av. Paulista",
            "equipmentType": "Radar Doppler",
            "measuredSpeed": "22.5 km/h",
            "measuredFlow": "1.420 veíc/h",
            "saturationDegree": "0,72",
            "occupancyRate": "64,0%",
            "inmetroReport": "INMETRO 9942/2025",
            "operationalStatus": "Operação Nominal",
            "is_enforcement": True,
            "purpose": "fiscalizacao",
        }
    ]
    report_data = {
        "sensors": sensors,
        "safetyInterventions": [],
    }

    formatter = AbntMarkdownReportFormatter()
    md = formatter.format(report_data)

    # Art. 1 § 2: must not contain 'prioritário'
    assert "prioritário" not in md
    assert "dever dos órgãos e entidades componentes do Sistema Nacional de Trânsito" in md

    # Art. 24: must cover both incisos II and III
    assert "Art. 24, incisos II e III" in md or "Artigo 24" in md
    assert "planejar, projetar, regulamentar e operar o trânsito" in md
    assert "implantar, manter e operar o sistema de sinalização" in md
