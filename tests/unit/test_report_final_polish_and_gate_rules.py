# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Unit tests for the 5 final polish points and 6 validation gate criteria:
1. All critical points appear in 1.2 and action recommendation, with radar+feed concordance.
2. Status count in summary matches actual critical stations count.
3. Radar measurement modality parity (pontual across Section 2 and cards).
4. Derived variable marking symmetry via canonical resolver.
5. Standardized volume label and units (veíc/h) for all sources.
6. No orphan braces in equation text and parameters.
7. Single consolidated rounding note footer in Annex I.
"""

import pytest
from src.formatters.abnt_markdown_formatter import AbntMarkdownReportFormatter
from src.validation.critical_points_gate_rule import CriticalPointsGateRule
from src.validation.equation_consistency_rule import EquationConsistencyRule
from src.report.derived_variable_resolver import DerivedVariableResolver


def _create_mixed_critical_scenario():
    return [
        {
            "id": "src1",
            "junction": "Rua Augusta",
            "equipmentType": "Visão Computacional (Câmera)",
            "measuredSpeed": "31.0 km/h",
            "saturationDegree": "0,65",
            "occupancyRate": "48,0%",
            "inmetroReport": "INMETRO 1001",
            "operationalStatus": "Fluxo Estável",
        },
        {
            "id": "src2",
            "junction": "Av. Paulista",
            "equipmentType": "Radar de Tráfego (Sensor Físico Doppler)",
            "measuredSpeed": "1.0 km/h",
            "saturationDegree": "0,96",
            "occupancyRate": "92,0%",
            "inmetroReport": "INMETRO 1002",
            "operationalStatus": "Crítico / Retenção Severa",
        },
        {
            "id": "src3",
            "junction": "Waze Feed",
            "equipmentType": "Feed de Terceiros (API / Crowdsourcing)",
            "measuredSpeed": "8.5 km/h",
            "saturationDegree": "0,92",
            "occupancyRate": "88,0%",
            "inmetroReport": "Dado Amostral de Terceiros",
            "operationalStatus": "Crítico / Retenção Severa",
        },
        {
            "id": "src4",
            "junction": "TomTom Feed",
            "equipmentType": "Feed de Terceiros (API / Crowdsourcing)",
            "measuredSpeed": "22.0 km/h",
            "saturationDegree": "0,68",
            "occupancyRate": "62,0%",
            "inmetroReport": "Dado Amostral de Terceiros",
            "operationalStatus": "Fluxo Estável",
        },
    ]


def test_gate_rule_critical_points_in_summary_and_action():
    """Validates that all critical stations appear in 1.2 and action recommendation."""
    sensors = _create_mixed_critical_scenario()
    formatter = AbntMarkdownReportFormatter()
    md = formatter.format({"sensors": sensors, "safetyInterventions": []})

    # Both src2 (radar) and src3 (feed) must appear in Section 1.2
    assert "src2" in md
    assert "src3" in md

    # Check non-repetitive critical points label
    assert "Pontos em regime crítico (2 de 4):" in md
    assert "Ponto Mais Crítico:" not in md

    # Check summary count
    assert "2 de 4 pontos em regime crítico" in md

    # Check concordance phrase
    assert "detector físico e o feed independente concordam" in md

    # Check action recommendation covers both
    assert "aproximação da estação **src2**" in md
    assert "trecho correspondente à estação **src3**" in md

    # Check Table 1.4 Velocidade (v) and metrological note
    assert "| Velocidade (v) |" in md
    assert "Nota Metrológica: Para fontes de velocidade pontual, o valor é usado como aproximação da velocidade espacial." in md

    # Check lowercase in station syntheses while keeping [Derivado por Modelo]
    assert "A velocidade pontual" in md or "a velocidade pontual" in md
    assert "volume de fluxo veicular [Derivado por Modelo]" in md or "o volume de fluxo veicular [Derivado por Modelo]" in md


def test_gate_rule_radar_measurement_pontual_parity():
    """Validates that radar speed is described as 'pontual' both in Section 2 and Annex I."""
    sensors = _create_mixed_critical_scenario()
    formatter = AbntMarkdownReportFormatter()
    md = formatter.format({"sensors": sensors, "safetyInterventions": []})

    # Section 2 radar description
    assert "Medições pontuais de velocidade instantânea" in md or "pontual" in md

    # Annex I radar card
    assert "Velocidade pontual de 1,0 km/h aferida por radar" in md
    assert "velocidade média espacial de 1,0 km/h aferida por radar" not in md


def test_derived_variable_resolver_symmetry():
    """Validates that DerivedVariableResolver produces consistent naming and tagging."""
    feed_occ = DerivedVariableResolver.get_feature_name("occupancy", is_feed=True)
    assert "[Derivado por Modelo]" in feed_occ
    assert "(%)" in feed_occ

    feed_flow = DerivedVariableResolver.get_feature_name("flow", is_feed=True)
    assert "[Derivado por Modelo]" in feed_flow
    assert "(veíc/h)" in feed_flow

    # In prose formatting
    occ_prose = DerivedVariableResolver.format_prose_mention(feed_occ, keep_derived_tag=True)
    assert occ_prose.startswith("a ")
    assert "taxa de ocupação da faixa" in occ_prose
    assert "[Derivado por Modelo]" in occ_prose

    flow_prose = DerivedVariableResolver.format_prose_mention(feed_flow, keep_derived_tag=True)
    assert flow_prose.startswith("o ")
    assert "volume de fluxo veicular" in flow_prose
    assert "[Derivado por Modelo]" in flow_prose


def test_gate_rule_blocks_missing_critical_point():
    """Validates that CriticalPointsGateRule halts emission if a critical point is omitted."""
    sensors = _create_mixed_critical_scenario()
    rule = CriticalPointsGateRule()

    # Artificially truncated markdown omitting src2
    corrupted_md = """## 1. RESUMO EM UMA PÁGINA
- Ponto Crítico: apenas a src3 em retenção.
- Ação Recomendada: verificar trecho src3.
## 2. O QUE O SISTEMA VIU
"""
    violations = rule.validate_post(corrupted_md, {"sensors": sensors})
    assert any("Estação Crítica Omitida" in v.title for v in violations)


def test_gate_rule_blocks_orphan_braces_in_equations():
    """Validates that EquationConsistencyRule catches orphan braces like 'a t-1}'."""
    rule = EquationConsistencyRule()
    broken_md = """#### A.5 Estimador Cinemático de Estado
$$ v_t = v_{t-1} + a_{t-1} \\cdot \\Delta t \\cdot e^{-\\lambda \\Delta t} \\tag{A.5} $$
Onde **v_t** é a velocidade e a t-1} é a aceleração precedente.
"""
    violations = rule.validate_post(broken_md, {})
    assert any("Chave Órfã" in v.title or "Sintaxe Inválida" in v.title for v in violations)


def test_annex_single_intro_rounding_note():
    """Validates that Annex I has the rounding note in its introduction before station cards."""
    sensors = _create_mixed_critical_scenario()
    formatter = AbntMarkdownReportFormatter()
    md = formatter.format({"sensors": sensors, "safetyInterventions": []})

    expected_note = "Os percentuais podem somar 100% ± 0,1 por arredondamento."
    assert expected_note in md
    assert md.count(expected_note) == 1

    # Ensure the note appears before the first station card
    idx_note = md.find(expected_note)
    idx_card1 = md.find("#### Estação 01")
    assert idx_note != -1
    assert idx_card1 != -1
    assert idx_note < idx_card1
