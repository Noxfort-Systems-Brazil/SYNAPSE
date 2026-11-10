# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Unit tests for ReportValidationGate negative assertions (Error Classes 1 to 6).
Validates unrendered leaks, weight contradiction, regime desync, typology,
confidence attenuation, and derived variable disclaimers.
"""

from src.validation.report_validation_gate import ReportValidationGate


def test_negative_class_1_unrendered_placeholder_and_internal_leak():
    report_data = {"sensors": [{"id": "S1", "equipmentType": "Radar"}]}

    violations_pl = ReportValidationGate.validate_post_markdown(
        "Disponibilidade de {avg_availability} consolidada.", report_data
    )
    assert any(v.error_class == 1 for v in violations_pl)

    violations_leak = ReportValidationGate.validate_post_markdown(
        "Fonte operando via SourceType.API em produção.", report_data
    )
    assert any(v.error_class == 1 for v in violations_leak)


def test_negative_class_2_station_synthesis_contradicts_weights():
    report_data = {
        "sensors": [
            {
                "id": "S1",
                "equipmentType": "Radar",
                "xai_weights": {"Velocidade": 0.40, "Densidade": 0.35, "Ocupação": 0.15, "Volume": 0.10},
                "station_narrative": "A seção operou com fluxo. A ocupação e o volume foram os principais fatores.",
            }
        ]
    }
    violations = ReportValidationGate.validate_pre_markdown(report_data)
    assert any(v.error_class == 2 for v in violations)


def test_negative_class_3_regime_and_status_contradiction():
    report_data = {
        "sensors": [
            {
                "id": "S1",
                "equipmentType": "Radar",
                "measuredSpeed": "2,0 km/h",
                "saturation": "0,95",
                "operational_status": "Livre / Fluido",
            }
        ]
    }
    violations = ReportValidationGate.validate_pre_markdown(report_data)
    assert any(v.error_class == 3 for v in violations)


def test_negative_class_4_source_typology_inconsistency():
    report_data = {
        "sensors": [
            {
                "id": "WAZE-01",
                "equipmentType": "Feed de Terceiros (API Waze)",
                "canonical_source_type": "third_party_feed",
                "speedLabel": "Velocidade Aferida",
            }
        ]
    }
    violations = ReportValidationGate.validate_pre_markdown(report_data)
    assert any(v.error_class == 4 for v in violations)


def test_negative_class_5_unattenuated_nonmetrological_recommendation():
    report_data = {
        "sensors": [
            {
                "id": "WAZE-01",
                "equipmentType": "Feed de Terceiros (API Waze)",
                "canonical_source_type": "third_party_feed",
                "measuredSpeed": "2,0 km/h",
                "saturation": "0,96",
            }
        ],
        "action_recommendation": "Ajustar tempos semafóricos prioritariamente no cruzamento.",
    }
    violations = ReportValidationGate.validate_pre_markdown(report_data)
    assert any(v.error_class == 5 for v in violations)


def test_negative_class_6_derived_variables_not_flagged():
    report_data = {
        "sensors": [
            {
                "id": "WAZE-01",
                "canonical_source_type": "third_party_feed",
            }
        ]
    }
    markdown_without_disclaimer = "## Seção 3: Atribuição de Pesos de IA [Derivado por Modelo]\n\nNenhuma menção técnica."
    violations = ReportValidationGate.validate_post_markdown(markdown_without_disclaimer, report_data)
    assert any(v.error_class == 6 for v in violations)
