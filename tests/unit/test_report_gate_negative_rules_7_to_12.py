# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Noxfort Systems <contato@noxfort.com>

"""
Unit tests for ReportValidationGate negative assertions (Error Classes 7 to 12)
and the 5 blocking gate tests (Severity tie-breaking, typology vocabulary,
Section 3 weight completeness, equation symbol linting, and label redundancy).
"""

from src.validation.report_validation_gate import ReportValidationGate


def test_negative_class_7_feature_weight_sum_mismatch():
    report_data = {
        "sensors": [
            {
                "id": "S1",
                "equipmentType": "Radar",
                "xai_weights": {"Velocidade": 0.40, "Densidade": 0.30},
            }
        ]
    }
    violations = ReportValidationGate.validate_pre_markdown(report_data)
    assert any(v.error_class == 7 for v in violations)


def test_negative_class_8_cross_section_data_contradiction():
    report_data = {
        "sensors": [
            {
                "id": "S1",
                "equipmentType": "Radar",
                "eval_count": 120,
                "approved_count": 110,
            }
        ],
        "executive_summary": {
            "consolidated_availability": 100.0,
        },
    }
    violations = ReportValidationGate.validate_pre_markdown(report_data)
    assert any(v.error_class == 8 for v in violations)


def test_negative_class_9_equation_lint_error():
    report_data = {"sensors": [{"id": "S1", "equipmentType": "Radar"}]}
    markdown_missing_eq = "## ANEXO TÉCNICO\n\n[Equação A.1]\n[Equação A.2]\n[Equação A.4]\n[Equação A.5]"
    violations = ReportValidationGate.validate_post_markdown(markdown_missing_eq, report_data)
    assert any(v.error_class == 9 for v in violations)


def test_negative_class_10_normative_applicability_violation():
    report_data = {
        "sensors": [
            {
                "id": "WAZE-01",
                "equipmentType": "Feed de Terceiros (API Waze)",
                "canonical_source_type": "third_party_feed",
            }
        ],
        "references": ["Resolução CONTRAN nº 798/2020"],
    }
    violations = ReportValidationGate.validate_pre_markdown(report_data)
    assert any(v.error_class == 10 for v in violations)


def test_negative_class_11_prohibited_absolute_term():
    report_data = {"sensors": [{"id": "S1", "equipmentType": "Radar"}]}
    markdown_with_prohibited = "Este laudo pericial garante que 100% da percepção é isenta com ausência de viés comprovada."
    violations = ReportValidationGate.validate_post_markdown(markdown_with_prohibited, report_data)
    assert any(v.error_class == 11 for v in violations)


def test_negative_class_12_grammar_and_duplicate_words():
    report_data = {"sensors": [{"id": "S1", "equipmentType": "Radar"}]}

    markdown_duplicate = "O monitoramento da Estação Estação 01 identificou lentidão."
    violations_dup = ReportValidationGate.validate_post_markdown(markdown_duplicate, report_data)
    assert any(v.error_class == 12 for v in violations_dup)

    markdown_plural = "Total registrado de 1 leituras no período."
    violations_pl = ReportValidationGate.validate_post_markdown(markdown_plural, report_data)
    assert any(v.error_class == 12 for v in violations_pl)


# ==============================================================================
# FIVE BLOCKING GATE TESTS FOR XAI REFINEMENTS
# ==============================================================================
def test_negative_prohibited_terms_normativo_canonico_oficial():
    report_data = {"sensors": [{"id": "S1", "equipmentType": "Radar"}]}
    for phrase in ["Critérios normativos de tráfego", "Valores canônicos adotados", "Relatório oficial homologado"]:
        md = f"Texto de teste contendo {phrase} para validação."
        violations = ReportValidationGate.validate_post_markdown(md, report_data)
        assert any(v.error_class == 11 for v in violations), f"Failed to block prohibited term in: '{phrase}'"


def test_blocking_gate_1_worst_criteria_severity():
    report_data = {
        "sensors": [
            {
                "id": "DET-01",
                "measuredSpeed": "1,2 km/h",
                "saturation": "0,35",
                "operational_status": "Estável / Monitoramento Preventivo",
            }
        ]
    }
    violations = ReportValidationGate.assert_worst_criteria_severity(report_data)
    assert len(violations) > 0
    assert violations[0].error_class == 3
    assert "Status Abaixo da Severidade do Pior Critério" in violations[0].title or "Contradição" in violations[0].title


def test_blocking_gate_2_source_typology_vocabulary():
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
    violations = ReportValidationGate.assert_vocabulary_matches_source_type(report_data)
    assert any(v.error_class == 4 for v in violations)

    report_pure_feed = {
        "sensors": [
            {
                "id": "WAZE-01",
                "equipmentType": "Feed de Terceiros (API Waze)",
                "canonical_source_type": "third_party_feed",
            }
        ]
    }
    md_feed_with_radar = "O radar físico do trecho registrou velocidade informada."
    violations_md = ReportValidationGate.assert_vocabulary_matches_source_type(
        report_pure_feed, markdown_text=md_feed_with_radar
    )
    assert any(v.error_class == 4 for v in violations_md)


def test_blocking_gate_3_section3_incomplete_weights():
    report_data = {"sensors": [{"id": "S1"}]}
    md_incomplete = """
## 3. POR QUE CHEGOU A ESSA CONCLUSÃO: FATORES DE MAIOR PESO (XAI)

| Estação / Ponto de Coleta | Fatores de Maior Peso (% Atribuição Neural) | Fator Preponderante |
| :--- | :--- | :--- |
| **Estação 01** | Velocidade (32,3%), Ocupação [Derivado por Modelo] (27,7%), Volume [Derivado por Modelo] (24,1%) | Velocidade |
"""
    violations = ReportValidationGate.assert_section3_matches_annex_cards(md_incomplete, report_data)
    assert len(violations) > 0
    assert any(v.error_class == 7 for v in violations)
    assert "Seção 3" in violations[0].title


def test_blocking_gate_4_equation_greek_symbols_lint():
    md_missing_lambda = """
## ANEXO TÉCNICO: FORMULAÇÃO MATEMÁTICA E EQUAÇÕES DE PERCEPÇÃO

#### A.5 Estimador Cinemático de Estado
$$ v_t = v_{t-1} + a_{t-1} \\cdot \\Delta t \\tag{A.5} $$
Onde **v_t** é a velocidade, **a_{t-1}** a aceleração, **Δt** o passo de amostragem e **λ** o amortecimento.
"""
    violations = ReportValidationGate.assert_equation_greek_symbols_match_text(md_missing_lambda)
    assert any(v.error_class == 9 and "λ" in v.message for v in violations)


def test_blocking_gate_5_label_description_redundancy():
    md_redundant = "O autoencoder convolucional Filtro de Ruído Convolucional (PI-DVAE) isolou ruído no sinal."
    violations = ReportValidationGate.assert_no_label_description_redundancy(md_redundant)
    assert len(violations) > 0
    assert any(v.error_class == 12 for v in violations)
    assert "Redundância Nominal" in violations[0].title
